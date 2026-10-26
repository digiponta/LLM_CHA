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
            self._append(chunk)
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

    def submit(self,text):
        if self.process is None or self.process.poll() is not None:return
        try:
            self.process.stdin.write(text+"\n")
            self.process.stdin.flush()
            self._append(text+"\n")
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
        self._append(f"[クリップボードを読み込みました（{len(content)}文字・一時文脈・未検証）。次の質問1回にのみ利用します。]\n")

    def send(self):
        value=self.entry.get().strip()
        if not value:return
        self.entry.delete(0,"end")
        query=google_query(value)
        if query:
            self._append(f"You> {value}\nAI> Googleで「{query}」を検索します。ブラウザのページをコピーし、「クリップボード読込」を押してください。\n")
            webbrowser.open("https://www.google.com/search?q="+quote_plus(query))
            return
        if self.clipboard_context and not value.startswith("/"):
            source=self.clipboard_context
            self.clipboard_context=""
            # Evidence stays unverified and only travels with this one turn.
            # CLI chat.py consumes one line per input; avoid newline-driven turns.
            flattened=" ".join(source.splitlines())
            request=("次の資料はクリップボードからの未検証の一時情報です。"
                     "資料の内容を事実として承認・学習せず、根拠がある範囲で回答してください。 "
                     "資料: "+flattened+" 質問: "+value)
            self.submit(request)
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
