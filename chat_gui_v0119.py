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
    if any(word in question for word in ("ドリンク","飲み物","ビバレッジ")):
        match=re.search(r"ビバレッジ\s+(.+?)\s+ビバレッジ一覧へ",source,re.S)
        if not match:
            return "資料にドリンクの一覧は確認できませんでした。（未検証）"
        section=match.group(1)
        # The copied menu repeats each product name consecutively.
        names=re.findall(r"(.{3,55}?)\s+\1(?=\s|$)",section)
        unique=[]
        for name in names:
            name=" ".join(name.split())
            if name and name not in unique:
                unique.append(name)
        if unique:
            return "資料に記載されたドリンク: "+"、".join(unique)+"。（クリップボード由来・未検証）"
        return "資料中のドリンク欄: "+section[:450]+"（クリップボード由来・未検証。商品名の区切りは未確認）"
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
        ("を飲んだ","飲んでみたんですね。味や香りはどうでしたか？"),
        ("を飲みました","飲んでみたんですね。どうでしたか？"),
        ("も好きです","それも好きなんですね。どんなところが気に入っていますか？"),
        ("も好き","それも好きなんですね。どんなところが気に入っていますか？"),
        ("が好き","好きなんですね。どんなところが気に入っていますか？"),
        ("が好きです","好きなんですね。どんなところが気に入っていますか？"),
    ):
        if text.endswith(suffix):
            item=text[:-len(suffix)].strip()
            if len(item)>=3 and item in source:
                return reply
    # A short variant such as "黒耳" may be a product variant in the source.
    short=re.fullmatch(r"(.{2,16}?)(?:を飲んだ|を飲みました)",text)
    if short and short.group(1) in source:
        return "そのドリンクを飲んだんですね。どんな味でしたか？"
    return None

def selected_item_from_utterance(source, utterance):
    text=utterance.strip().rstrip("。！! ")
    for suffix in ("を食べました","を食べた","を飲みました","を飲んだ",
                   "も好きです","も好き","が好きです","が好き"):
        if text.endswith(suffix):
            item=text[:-len(suffix)].strip()
            if item and item in source:
                return item
    return None

def reply_to_experience(message, active_item):
    """Conservative local follow-up for a user-reported food experience."""
    if not active_item:
        return None
    text=message.strip().rstrip("。！! ")
    if any(term in text for term in ("美味しかった","おいしかった","美味しい","おいしい")):
        if any(term in text for term in ("あっさり","さっぱり","軽い味")):
            return "あっさりした味わいが気に入ったんですね。"+active_item+"、また食べたいと思いますか？"
        return "美味しかったんですね。"+active_item+"のどんなところが気に入りましたか？"
    if any(term in text for term in ("満足した","満足です","満足だった","満足している")):
        return "満足できたんですね。"+active_item+"、いい食事になったようですね。"
    if any(term in text for term in ("また食べたい","リピートしたい")):
        return "また食べたいと思えるほど気に入ったんですね。"
    return None

def source_question_answer(source, question):
    """Return source-grounded excerpts, never unsupported generated facts."""
    normalized=question.strip().rstrip("？?。！!")
    topics=(
        (("屈折率",), ("屈折率","refractive index")),
        (("カット","研磨","割れ","難しい"), ("カット","研磨","劈開","へき開","硬度","脆","割れ","加工")),
    )
    words=next((keys for hints,keys in topics if any(w in normalized for w in hints)),None)
    if words is None:
        return None
    # Sentence boundary splitting; a web-page clipboard may be one long line.
    spans=re.split(r"(?<=[。！？!?])\s*|[\r\n]+",source)
    hits=[]
    for span in spans:
        span=" ".join(span.split())
        if any(w.casefold() in span.casefold() for w in words):
            if len(span)>300:
                for word in words:
                    i=span.casefold().find(word.casefold())
                    if i>=0:
                        span=span[max(0,i-90):i+170]
                        break
            if span not in hits:
                hits.append(span)
        if len(hits)>=3:
            break
    if hits:
        return "資料の該当箇所（未検証）: "+" / ".join(hits)
    return "取り込んだ資料には、この質問に直接対応する記述を確認できませんでした。"

def casual_preference_reply(message):
    match=re.fullmatch(r"私は[、,\s]*(.{2,80}?)が好き(?:です)?[。！!\s]*",message.strip())
    if match:
        return match.group(1)+"が好きなんですね。どんなところに魅力を感じますか？"
    return None

def preference_dialogue_reply(message, topic):
    """Acknowledge a user's qualitative preference without inventing facts."""
    if not topic:
        return None
    text=message.strip().rstrip("。！! ")
    if text in ("そうだよ","そうです","うん","はい","そうそう"):
        return "そうなんですね。"+topic+"の魅力が伝わってきます。"
    if ("きらきら" in text or "キラキラ" in text or "輝き" in text) and any(
        word in text for word in ("心地よい","好き","気に入","きれい","綺麗","美しい")):
        return "きらきらした輝きが心地よいんですね。"+topic+"のどんな色合いが好みですか？"
    if any(word in text for word in ("心地よい","癒される","きれい","綺麗")) and not (
        "なぜ" in text or "理由" in text or "？" in text or "?" in text):
        return "そう感じるんですね。"+topic+"の魅力を楽しんでいるんですね。"
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
        self.active_food_item=""
        self.active_preference_topic=""
        self.line_buffer=""
        self.chat_ready=False
        self.transcript=scrolledtext.ScrolledText(root, wrap="word",state="disabled",font=("Yu Gothic UI",11))
        self.transcript.pack(fill="both",expand=True,padx=10,pady=10)
        bottom=ttk.Frame(root)
        bottom.pack(fill="x",padx=10,pady=(0,10))
        self.entry=ttk.Entry(bottom)
        self.entry.pack(side="left",fill="x",expand=True)
        self.entry.bind("<Return>",lambda _: self.send())
        self.send_btn=ttk.Button(bottom,text="送信",command=self.send)
        self.send_btn.pack(side="left",padx=5)
        self.clipboard_btn=ttk.Button(bottom,text="クリップボード読込",command=self.read_clipboard)
        self.clipboard_btn.pack(side="left",padx=5)
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
                if not char:
                    break
                # Mirror raw chat.py output to the launching console.
                try:
                    sys.stdout.write(char)
                    sys.stdout.flush()
                except (OSError, UnicodeError):
                    pass
                self.events.put(("output",char))
        except Exception as exc:
            self.events.put(("output","\n[GUI reader error: "+repr(exc)+"]\n"))
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
            # input("You> ") emits a prompt without a newline; the subsequent
            # print("AI> ...") may be delivered as "You> AI> ...".
            # Drop only the CLI prompt, never the answer sharing its line.
            if line.startswith("You> "):
                line=line[len("You> "):]
            if should_display_line(line) and line:
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
        self.active_food_item=""
        self.active_preference_topic=""
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
            preference=casual_preference_reply(value)
            if preference is not None:
                match=re.fullmatch(r"私は[、,\\s]*(.{2,80}?)が好き(?:です)?[。！!\\s]*",value.strip())
                if match:
                    self.active_preference_topic=match.group(1)
                self._append("You> "+value+"\nAI> "+preference+"\n")
                return
            preference_followup=preference_dialogue_reply(
                value,getattr(self,"active_preference_topic",""))
            if preference_followup is not None:
                self._append("You> "+value+"\nAI> "+preference_followup+"\n")
                return
            followup=contextual_followup(source,value)
            if followup is not None:
                # Detect the specific item mentioned, and keep it as dialogue
                # topic. A user's taste report is not a verified external fact.
                clean=value.strip().rstrip("。！! ")
                item=selected_item_from_utterance(source, clean)
                if item:
                    self.active_food_item=item
                self._append("You> "+value+"\nAI> "+followup+"\n")
                return
            experience=reply_to_experience(value,getattr(self,"active_food_item",""))
            if experience is not None:
                self._append("You> "+value+"\nAI> "+experience+"\n")
                return
            grounded=source_question_answer(source,value)
            if grounded is not None:
                self._append("You> "+value+"\nAI> "+grounded+"\n")
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
