#!/usr/bin/env python3
"""Tkinter GUI wrapper around the existing CLI chat.py session.

The GUI sends ordinary lines to the unmodified input protocol, and shows
stdout incrementally. chat.py remains the single source of inference logic.
"""
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
from pathlib import Path
from chat_runtime_status_v0135882 import status_text

ROOT=Path(__file__).resolve().parent

class ChatGUI:
    def __init__(self,root):
        self.root=root
        root.title("LLM_CHA Chat — v0.13.58.82")
        root.geometry("920x660")
        self.proc=None
        self.out=queue.Queue()
        self.view=scrolledtext.ScrolledText(root,wrap="word",state="disabled",font=("Consolas",11))
        self.view.pack(fill="both",expand=True,padx=8,pady=8)
        toolbar=tk.Frame(root)
        toolbar.pack(fill="x",padx=8)
        self.entry=tk.Entry(toolbar,font=("Yu Gothic UI",12))
        self.entry.pack(side="left",fill="x",expand=True)
        self.entry.bind("<Return>",lambda e:self.send())
        tk.Button(toolbar,text="送信",command=self.send).pack(side="left",padx=3)
        tk.Button(toolbar,text="/status",command=self.status).pack(side="left",padx=3)
        tk.Button(toolbar,text="再起動",command=self.restart).pack(side="left",padx=3)
        self.root.protocol("WM_DELETE_WINDOW",self.close)
        self.launch()
        root.after(50,self.drain)

    def append(self,txt):
        self.view.configure(state="normal")
        self.view.insert("end",txt)
        self.view.see("end")
        self.view.configure(state="disabled")

    def launch(self):
        # -u is necessary: prompt 'You> ' has no newline in chat.py.
        self.proc=subprocess.Popen([sys.executable,"-u",str(ROOT/"chat.py")],
            cwd=str(ROOT),stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,bufsize=0)
        process=self.proc
        def reader():
            decoder=__import__("codecs").getincrementaldecoder("utf-8")("replace")
            try:
                while True:
                    raw=process.stdout.read(1)
                    if not raw:break
                    txt=decoder.decode(raw)
                    if txt:self.out.put(txt)
                tail=decoder.decode(b"",final=True)
                if tail:self.out.put(tail)
            except (OSError,ValueError) as exc:
                self.out.put("\n[reader error: "+str(exc)+"]\n")
            finally:self.out.put("\n[chat process stopped]\n")
        threading.Thread(target=reader,daemon=True).start()

    def drain(self):
        chunks=[]
        try:
            while len(chunks)<4096:chunks.append(self.out.get_nowait())
        except queue.Empty:pass
        if chunks:self.append("".join(chunks))
        self.root.after(50,self.drain)

    def send(self):
        text=self.entry.get().strip()
        if not text:return
        if not self.proc or self.proc.poll() is not None:
            messagebox.showwarning("LLM_CHA","Chatプロセスが起動していません")
            return
        try:
            self.proc.stdin.write((text+"\n").encode("utf-8"))
            self.proc.stdin.flush()
        except (OSError,ValueError):
            messagebox.showerror("LLM_CHA","Chatへの送信に失敗しました")
            return
        self.entry.delete(0,"end")
        self.append("\n[送信] "+text+"\n")

    def status(self):
        self.append("\n"+status_text(ROOT)+"\n")
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.stdin.write(b"/status\n")
                self.proc.stdin.flush()
            except (OSError,ValueError):pass

    def stop(self):
        if not self.proc:return
        p=self.proc
        if p.poll() is None:
            try:p.stdin.write(b"/exit\n");p.stdin.flush()
            except (OSError,ValueError):pass
            try:p.wait(timeout=2)
            except subprocess.TimeoutExpired:
                p.terminate()
                try:p.wait(timeout=2)
                except subprocess.TimeoutExpired:p.kill()
        try:
            if p.stdin:p.stdin.close()
            if p.stdout:p.stdout.close()
        except OSError:pass
        self.proc=None

    def restart(self):
        self.stop()
        self.append("\n[restarting chat]\n")
        self.launch()

    def close(self):
        self.stop()
        self.root.destroy()

if __name__=="__main__":
    root=tk.Tk()
    ChatGUI(root)
    root.mainloop()
