"""Experimental Tkinter frontend for chat.py + Human-in-the-Loop reconciliation.

Run: python chat_gui_v0119.py
The existing chat.py handles all routing, evidence, memory and decisions.
This GUI only transports stdin/stdout and never changes knowledge directly.
"""
import os
import queue
import subprocess
import sys
import re
from html import unescape
import webbrowser
from urllib.parse import quote_plus
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from pathlib import Path

CHOICES=("prefer_a","prefer_b","both_contextual","neither","skip")

def google_query(text):
    match=re.fullmatch(r"\s*(.+?)\s*(?:を)?(?:ググって|ぐぐって|googleで検索して|Googleで検索して)\s*[。！!]*",text)
    return match.group(1).strip() if match else None

def should_display_line(line):
    stripped=line.strip()
    if not stripped:
        return True
    if stripped.startswith(("[normalized input:", "[candidate=", "[gate=", "[0 generated",
                             "[semantic reconciliation enabled:", "[Nagato Semantic Memory:",
                             "[use /sleep", "[decode-factory]")):
        return False
    if re.match(r"^\[\d+ generated probe tokens",stripped):
        return False
    return not stripped.startswith(("Device ", "GPU ", "Model ", "Tokenizer ", "Vocabulary size ",
                                    "Parameters ", "Context length ", "d_model ", "Layers ",
                                    "Attention heads ", "Checkpoint ", "Unknown reject ",
                                    "Probe count ", "Min confidence ", "Min token ",
                                    "Min mean ", "Min agreement ", "Min sem ",
                                    "Min int ", "Fallback ", "Context policy ",
                                    "Teaching queue ", "Knowledge queue ",
                                    "Gate review ", "Proposition db ", "Subject index ",
                                    "Typed index ", "Corpus memory ", "Conditional db ",
                                    "Cond candidates ", "Concept calib ", "Centroid source ",
                                    "Holdout in fit ", "Binding version "))

def clipboard_answer(source, question):
    """Extract a grounded food list; do not send a long document to 512-token LLM."""
    if "メニュー" in question and "フード" not in question:
        categories=[name for name in ("ビバレッジ","フード","コーヒー豆","ティー・紅茶","タンブラー","グッズ") if name in source]
        if categories:
            return "資料に記載されたメニューのカテゴリー: "+"、".join(categories)+"。（クリップボード由来・未検証）"
    if "フード" in question and ("種類" in question or "メニュー" in question):
        match=re.search(r"フード\s+(.+?)\s+フード一覧へ",source,re.S)
        if not match:
            return "取り込んだ資料には、フードの一覧を確認できません。"
        food=match.group(1)
        # Page text repeats each product twice; dedupe adjacent runs.
        items=re.findall(r"([^。]+?(?:サンド|モンブラン|アップルパイ|ケーキ))",food)
        clean=[]
        for item in items:
            item=" ".join(item.strip().split())
            if len(item)>75:
                item=item[-75:]
            if item and item not in clean:
                clean.append(item)
        if clean:
            return "取り込んだ資料に記載のフード: "+"、".join(clean)+"。（クリップボード由来・未検証）"
        return "資料にフード欄はありますが、商品名を安全に抽出できませんでした。"
    return "資料は一時文脈として読み込みましたが、この質問は資料から安全に抽出できません。質問を具体化するか、資料の該当部分を示してください。"

def contextual_followup(source, message):
    """Only respond locally when user's mentioned item occurs in copied text.

    Treat eating/liking as personal remarks, not as factual evidence.
    """
    text=message.strip().rstrip("。！!")
    for suffix,reply in (
        ("を食べた","そうなんですね。食べてみて、味や食感はどうでしたか？"),
        ("を食べました","そうなんですね。食べてみて、どうでしたか？"),
        ("が好き","好きなんですね。どんなところが気に入っていますか？"),
        ("が好きです","好きなんですね。どんなところが気に入っていますか？"),
    ):
        if text.endswith(suffix):
            item=text[:-len(suffix)].strip()
            if len(item)>=3 and item in source:
                return reply
    return None

def launch_command():
    return [sys.executable, "-u", str(Path(__file__).resolve().parent / "chat.py")]

class ChatGUI:
    def __init__(self, root):
        self.root=root
        root.title("LLM_CHA — Chat + Semantic Reconciliation (experimental)")
        root.geometry("920x700")
        self.events=queue.Queue()
        self.process=None
        self.awaiting_decision=False
        self.awaiting_context=False
        self.output_tail=""
        self.clipboard_context=""
        self.last_clipboard_source=""
        self.line_buffer=""
        self.chat_ready=False
        self.transcript=scrolledtext.ScrolledText(root, wrap="word",state="disabled",font=("Yu Gothic UI",11))
        self.transcript.pack(fill="both",expand=True,padx=10,pady=10)
        bottom=ttk.Frame(root)
        bottom.pack(fill="x",padx=10,pady=(0,10))
        self.entry=ttk.Entry(bottom)
        self.entry.pack(side="left",fill="x",expand=True)
        self.entry.bind("<Return>",lambda _: self.send())
        self.clipboard_btn=ttk.Button(bottom,text="クリップボード読込",command=self.read_clipboard)
        self.clipboard_btn.pack(side="left",padx=5)
        self.send_btn=ttk.Button(bottom,text="送信",command=self.send)
        self.send_btn.pack(side="left",padx=5)
        self.decisions=ttk.Frame(root)
        self.decisions.pack(fill="x",padx=10,pady=(0,10))
        for choice in CHOICES:
            btn=ttk.Button(self.decisions,text=choice,command=lambda c=choice:self.submit(c))
            btn.pack(side="left",padx=3)
        self._set_decisions(False)
        self.start()
        root.after(50,self.poll)
        root.protocol("WM_DELETE_WINDOW",self.close)

    def _append(self,text):
        self.transcript.configure(state="normal")
        self.transcript.insert("end",text)
        self.transcript.see("end")
        self.transcript.configure(state="disabled")

    def _set_decisions(self,enabled):
        for widget in self.decisions.winfo_children():
            widget.configure(state="normal" if enabled else "disabled")

    def start(self):
        env=os.environ.copy()
        env["LLM_CHA_RECONCILIATION"]="1"
        env["PYTHONUNBUFFERED"]="1"
        env["PYTHONIOENCODING"]="utf-8"
        env["PYTHONUTF8"]="1"
        creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0)
        try:
            self.process=subprocess.Popen(
                launch_command(),cwd=Path(__file__).resolve().parent,
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,encoding="utf-8",errors="replace",
                bufsize=1,env=env,creationflags=creationflags)
        except OSError as exc:
            messagebox.showerror("chat.py起動失敗",str(exc))
            self.send_btn.configure(state="disabled")
            return
        threading.Thread(target=self._reader,daemon=True).start()

    def _reader(self):
        try:
            while True:
                char=self.process.stdout.read(1)
                if not char:break
                self.events.put(("output",char))
        finally:
            self.events.put(("exit",self.process.poll()))

    def poll(self):
        parts=[]
        for _ in range(4096):
            try:
                kind,data=self.events.get_nowait()
            except queue.Empty:
                break
            if kind=="output":parts.append(data)
            elif kind=="exit":
                parts.append("\n[chat.py process terminated]\n")
                self.send_btn.configure(state="disabled")
                self._set_decisions(False)
        if parts:
            chunk="".join(parts)
            self._show_filtered(chunk)
            self.output_tail=(self.output_tail+chunk)[-500:]
            # CLI input() prompts may not be newline-terminated.
            if "Decision [prefer_a/prefer_b/both_contextual/neither/skip]>" in self.output_tail:
                self.awaiting_decision=True
                self._set_decisions(True)
            elif self.output_tail.rstrip().endswith("Context>"):
                self.awaiting_context=True
                self.awaiting_decision=False
                self._set_decisions(False)
            elif self.output_tail.rstrip().endswith("You>"):
                self.awaiting_context=False
                self.awaiting_decision=False
                self._set_decisions(False)
        self.root.after(50,self.poll)

    def _show_filtered(self, chunk):
        """Show dialogue only; retain CLI prompts and reconciliation choices."""
        self.line_buffer += chunk
        if not self.chat_ready:
            marker=self.line_buffer.find("You> ")
            if marker<0:
                self.line_buffer=self.line_buffer[-1000:]
                return
            self.chat_ready=True
            self.line_buffer=self.line_buffer[marker:]
        while "\n" in self.line_buffer:
            line,self.line_buffer=self.line_buffer.split("\n",1)
            if should_display_line(line) and not line.startswith("You> "):
                self._append(line+"\n")
        # CLI prompts have no trailing newline.
        if self.line_buffer in ("Context> ",) or self.line_buffer.startswith("Decision ["):
            self._append(self.line_buffer)
            self.line_buffer=""

    def submit(self,text, *, display=True):
        if self.process is None or self.process.poll() is not None:return
        try:
            self.process.stdin.write(text+"\n")
            self.process.stdin.flush()
            if display:
                self._append("You> "+text+"\n")
            self.output_tail=""
            self.awaiting_decision=False
            self._set_decisions(False)
            if text=="both_contextual":
                self.awaiting_context=True
            elif text in CHOICES:
                self.awaiting_context=False
        except (BrokenPipeError,OSError):
            messagebox.showerror("送信失敗","chat.pyとの接続が切断されました。")

    def read_clipboard(self):
        """Retain clipboard text as temporary, unverified context (not training)."""
        try:
            content=self.root.clipboard_get()
        except tk.TclError:
            messagebox.showwarning("クリップボード読込", "テキスト形式のクリップボードが見つかりません。")
            return
        if not isinstance(content,str) or not content.strip():
            messagebox.showwarning("クリップボード読込", "クリップボードのテキストが空です。")
            return
        self.clipboard_context=content[:20000]
        self.last_clipboard_source=self.clipboard_context
        self._append(f"[クリップボードを読み込みました（{len(content)}文字・一時文脈・未検証）。新しい資料を読むまで参照できます。]\n")

    def send(self):
        value=self.entry.get().strip()
        if not value:return
        self.entry.delete(0,"end")
        query=google_query(value)
        if query:
            self._append(f"You> {value}\nAI> Googleで「{query}」を検索します。ブラウザのページをコピーし、「クリップボード読込」を押してください。\n")
            webbrowser.open("https://www.google.com/search?q="+quote_plus(query))
            return
        # Persist clipboard evidence across follow-up turns; do not silently
        # consume it after an unsupported generic question.
        source=getattr(self,'last_clipboard_source','') or self.clipboard_context
        if source and not value.startswith("/"):
            followup=contextual_followup(source,value)
            if followup is not None:
                self._append("You> "+value+"\nAI> "+followup+"\n")
                return
            answer=clipboard_answer(source,value)
            if answer and not answer.startswith("資料は一時文脈として"):
                self._append("You> "+value+"\nAI> "+answer+"\n")
                return
            # Do not send the user's source-dependent question to the
            # ungrounded model as if no clipboard context existed.
            self._append("You> "+value+"\nAI> 資料のどの部分について知りたいですか？（一時資料は保持しています。）\n")
            return
        self.submit(value)

    def close(self):
        if self.process and self.process.poll() is None:
            try:self.process.stdin.write("/exit\n");self.process.stdin.flush()
            except OSError:pass
            if self.process.poll() is None:self.process.terminate()
        self.root.destroy()

if __name__=="__main__":
    window=tk.Tk()
    ChatGUI(window)
    window.mainloop()
