#!/usr/bin/env python3
"""LLM_CHA GUI: Japanese chat view backed by the existing chat.py runtime.

CLI stdout is preserved in a separate diagnostic tab. All pipe traffic is UTF-8.
"""
import codecs
import os
import queue
import re
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk, simpledialog
import webbrowser
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from chat_runtime_status_v0135882 import status_text
from natural_tool_router_v01358823 import route
from temporary_evidence_v01358824 import TemporaryEvidence
from general_evidence_retrieval_v01358827 import retrieve
from social_dialogue_bridge_v01358828 import social_reply
from causal_evidence_retrieval_v01358829 import retrieve_cause
from preference_dialogue_v013588210 import PreferenceContext
from unified_dialogue_context_v013588211 import UnifiedDialogueContext
from auto_wiki_unknown_v013588212 import is_unknown_answer, format_result
from wiki_full_article_v013588214 import resolve_full

ROOT = Path(__file__).resolve().parent
PROMPT = "You> "
DIAGNOSTIC = re.compile(
    r"^\s*(?:\[|(?:[0-9]+ generated probe tokens)|(?:Device|Model|Tokenizer|GPU|Parameters|Context length)\s*:)"
)


class ChatGUI:
    def __init__(self, root):
        self.root = root
        root.title("LLM_CHA — Chat")
        root.geometry("900x680")
        self.proc = None
        self.out = queue.Queue()
        self.pending = ""
        self.booted = False
        self.evidence = TemporaryEvidence()
        self.preference_context = PreferenceContext()
        self.dialogue_context = UnifiedDialogueContext()
        self.recent_products = []
        self.pending_llm_questions = queue.Queue()
        self.wiki_inflight = False
        self.header = ttk.Frame(root, padding=(12, 10))
        self.header.pack(fill="x")
        ttk.Label(self.header, text="LLM_CHA Chat", font=("Yu Gothic UI", 17, "bold")).pack(side="left")
        self.status_label = ttk.Label(self.header, text="起動中")
        self.status_label.pack(side="right")
        self.semantic_label = ttk.Label(self.header, text="Semantic: 初期化中")
        self.semantic_label.pack(side="right", padx=(0,16))

        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=4)
        self.conversation = scrolledtext.ScrolledText(
            self.tabs, wrap="word", state="disabled",
            font=("Yu Gothic UI", 12), padx=12, pady=10)
        self.diagnostics = scrolledtext.ScrolledText(
            self.tabs, wrap="word", state="disabled",
            font=("Consolas", 10), padx=8, pady=8)
        self.tabs.add(self.conversation, text="会話")
        self.tabs.add(self.diagnostics, text="ログ・コマンド")
        self.evidence_view = scrolledtext.ScrolledText(
            self.tabs, wrap="word", state="disabled",
            font=("Yu Gothic UI", 10), padx=10, pady=8)
        self.tabs.add(self.evidence_view, text="Evidence")
        self.conversation.tag_configure("user", foreground="#2159a4", spacing1=12)
        self.conversation.tag_configure("assistant", spacing1=10)
        self.conversation.tag_configure("system", foreground="#5c6571")

        bar = ttk.Frame(root, padding=10)
        bar.pack(fill="x")
        self.entry = ttk.Entry(bar, font=("Yu Gothic UI", 12))
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda event: self.send())
        ttk.Button(bar, text="送信", command=self.send).pack(side="left", padx=4)
        ttk.Button(bar, text="ググる", command=self.google).pack(side="left", padx=3)
        ttk.Button(bar, text="クリップ読込", command=self.clipboard_read).pack(side="left", padx=3)
        ttk.Button(bar, text="状態", command=self.status).pack(side="left", padx=3)
        ttk.Button(bar, text="再起動", command=self.restart).pack(side="left", padx=4)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.launch()
        root.after(50, self.drain)
        self.entry.focus_set()

    @staticmethod
    def add(widget, text, tag=None):
        widget.configure(state="normal")
        widget.insert("end", text, tag)
        widget.see("end")
        widget.configure(state="disabled")

    def launch(self):
        env = os.environ.copy()
        env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                   LLM_CHA_GUI_UTF8="1")
        self.pending = ""
        self.booted = False
        self.status_label.configure(text="起動中")
        self.proc = subprocess.Popen(
            [sys.executable, "-u", str(ROOT / "chat.py")],
            cwd=str(ROOT), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, bufsize=0, env=env)
        process = self.proc

        def reader():
            decoder = codecs.getincrementaldecoder("utf-8")("replace")
            try:
                while True:
                    data = process.stdout.read(256)
                    if not data:
                        break
                    text = decoder.decode(data)
                    if text:
                        self.out.put(("text", text))
                tail = decoder.decode(b"", final=True)
                if tail:
                    self.out.put(("text", tail))
            except (OSError, ValueError) as exc:
                self.out.put(("text", "\n[reader error: {}]\n".format(exc)))
            finally:
                self.out.put(("ended", process))
        threading.Thread(target=reader, daemon=True).start()

    def process_output(self, chunk):
        self.add(self.diagnostics, chunk)
        self.pending += chunk
        # CLI prompts aren't newline terminated; force flushing on prompt.
        while True:
            prompt_at = self.pending.find(PROMPT)
            newline_at = self.pending.find("\n")
            if prompt_at >= 0 and (newline_at < 0 or prompt_at < newline_at):
                before = self.pending[:prompt_at]
                self.pending = self.pending[prompt_at + len(PROMPT):]
                if before:
                    self.route_line(before)
                self.booted = True
                self.status_label.configure(text="対話可能")
                continue
            if newline_at < 0:
                break
            line = self.pending[:newline_at].rstrip("\r")
            self.pending = self.pending[newline_at + 1:]
            self.route_line(line)

    def route_line(self, line):
        line = line.strip()
        match = re.search(r"\[Nagato Semantic Memory:.*?internalized=(\d+),\s*pending=(\d+)", line)
        if match:
            self.semantic_label.configure(
                text=f"Trusted internalized: {match.group(1)}  Pending: {match.group(2)}")
        if not line:
            return
        if line.startswith("AI>"):
            answer = line[3:].strip()
            try:
                question = self.pending_llm_questions.get_nowait()
            except queue.Empty:
                question = ""
            if question and is_unknown_answer(answer):
                self.add(self.conversation,"システム: 未学習のためWikipediaを検索しています。\n","system")
                self.auto_wiki(question)
            else:
                self.add(self.conversation,"AI: "+answer+"\n","assistant")
        elif self.booted and not (DIAGNOSTIC.match(line) or line.startswith("You>")
                                 or line.startswith("PS ") or line.startswith("/")):
            # Unclassified output is kept in diagnostic tab, not silently interpreted as AI.
            pass

    def drain(self):
        for _ in range(1500):
            try:
                kind, data = self.out.get_nowait()
            except queue.Empty:
                break
            if kind == "text":
                self.process_output(data)
            elif kind == "auto_wiki":
                self.add(self.diagnostics, "[自動Wikipedia] "+data["status"]+"\n")
                self.add(self.conversation,format_result(data),"assistant")
                self.wiki_inflight=False
            elif kind == "wiki":
                self.add(self.diagnostics, data)
            elif kind == "wiki_evidence":
                topic, text = data
                self.evidence.add(text, "Wikipedia", topic=topic,
                                  source_title="日本語Wikipedia: "+topic,
                                  source_url="https://ja.wikipedia.org/w/index.php?"+urlencode({"search":topic}))
                self.refresh_evidence()
            elif data is self.proc:
                self.status_label.configure(text="終了")
                if self.pending:
                    self.route_line(self.pending)
                    self.pending = ""
                self.add(self.diagnostics, "\n[chat process stopped]\n")
        self.root.after(50, self.drain)

    def send(self):
        text = self.entry.get().strip()
        if not text:
            return
        # Multi-topic reference resolution, before knowledge/social routing.
        recovered=self.dialogue_context.resolve(text)
        if recovered:
            self.dialogue_context.switch(recovered)
            self.evidence.set_topic(recovered)
            self.preference_context.set_topic(recovered)
            self.add(self.conversation,"システム: 話題を「"+recovered+"」に戻しました。\n","system")
            # Discard the anaphoric prefix but preserve the actual preference.
            text=re.sub(r"^(?:さっき|先ほど|前に).{0,10}(?:宝石|石)の?","",text).strip()
            if not text:
                self.entry.delete(0,"end")
                return
        intent=route(text)
        if intent is None:
            causal=retrieve_cause(self.evidence,text)
            if causal is not None:
                self.add(self.conversation,"あなた: "+text+"\n","user")
                if causal["status"]=="SUPPORTED_EXCERPT":
                    self.add(self.conversation,
                             "AI: 【外部未検証資料："+causal["source"]+"】資料に次の理由説明があります。\n"
                             +"  引用: "+causal["quote"]+"\n","assistant")
                elif causal["status"]=="NO_EVIDENCE":
                    self.add(self.conversation,"AI: 話題に対応する一時資料がありません。関連資料をクリップ読込してください。\n","system")
                elif causal["status"]=="NO_TOPIC":
                    self.add(self.conversation,"AI: 理由を調べたい対象を指定してください。\n","system")
                else:
                    self.add(self.conversation,"AI: 一時資料から質問に対応する因果関係を確認できません。推測による理由説明は控えます。\n","system")
                self.entry.delete(0,"end")
                return
        if intent is None:
            evidence_answer=self.evidence.answer(text)
            if evidence_answer is not None:
                self.add(self.conversation,"あなた: "+text+"\n","user")
                self.add(self.conversation,"AI: "+evidence_answer+"\n","assistant")
                detail=self.evidence.lookup(text)
                if detail:
                    self.add(self.conversation,"  根拠: "+detail["quote"]+"\n","system")
                self.entry.delete(0,"end")
                return
        if intent is None:
            result=retrieve(self.evidence,text)
            if result is not None:
                self.add(self.conversation,"あなた: "+text+"\n","user")
                if result["status"]=="EXCERPTS":
                    self.recent_products = [x.strip() for x in result["quotes"] if x.strip()][:8]
                    self.add(self.conversation,
                             "AI: 【外部未検証資料："+result["source"]+"】"
                             +result["topic"]+"について、資料に次の記載があります。\n"
                             +"\n".join("  引用: "+q for q in result["quotes"])+"\n",
                             "assistant")
                elif result["status"]=="NO_EVIDENCE":
                    self.add(self.conversation,
                             "AI: "+result["topic"]+"の検索結果は、まだ一時資料として読み込まれていません。"
                             "ブラウザーの関連文章をコピーして「クリップ読込」を実行してください。\n",
                             "system")
                else:
                    self.add(self.conversation,
                             "AI: 一時資料に質問へ直接答えられる記述が見つかりません。"
                             "関連するメニューやフードの説明をコピーしてください。\n",
                             "system")
                self.entry.delete(0,"end")
                return
        if intent is None:
            preference_reply=self.preference_context.respond(text)
            if preference_reply is not None:
                self.add(self.conversation,"あなた: "+text+"\n","user")
                self.add(self.conversation,"AI: "+preference_reply+"\n","assistant")
                self.entry.delete(0,"end")
                return
        if intent is None:
            reply=social_reply(text, self.evidence.topic, self.recent_products)
            if reply is not None:
                self.add(self.conversation,"あなた: "+text+"\n","user")
                self.add(self.conversation,"AI: "+reply+"\n","assistant")
                self.entry.delete(0,"end")
                return
        if intent is not None:
            if intent.query:
                self.recent_products = []
                self.dialogue_context.switch(intent.query)
                self.evidence.set_topic(intent.query)
                self.preference_context.set_topic(intent.query)
            self.entry.delete(0,"end")
            self.add(self.conversation,"あなた: "+text+"\n","user")
            if intent.action=="GOOGLE":
                self.entry.insert(0,intent.query)
                self.google()
                self.entry.delete(0,"end")
                self.add(self.conversation,"システム: Google検索をブラウザーで開きました。\n","system")
            elif intent.action=="WIKI":
                self.entry.insert(0,intent.query)
                self.wiki_search()
                self.entry.delete(0,"end")
                self.add(self.conversation,"システム: Wikipediaを検索しています。結果はログに表示します。\n","system")
            elif intent.action=="CLIPBOARD":
                self.clipboard_read()
            return
        if self.proc is None or self.proc.poll() is not None:
            messagebox.showwarning("LLM_CHA", "Chatプロセスが起動していません")
            return
        try:
            self.proc.stdin.write((text + "\n").encode("utf-8"))
            self.proc.stdin.flush()
        except (OSError, ValueError):
            messagebox.showerror("LLM_CHA", "送信できませんでした")
            return
        self.pending_llm_questions.put(text)
        self.add(self.conversation, "あなた: " + text + "\n", "user")
        self.entry.delete(0, "end")


    def auto_wiki(self, question):
        def worker():
            result=resolve_full(question,self.evidence.topic)
            self.out.put(("auto_wiki",result))
        threading.Thread(target=worker,daemon=True).start()

    def google(self):
        query=self.entry.get().strip() or simpledialog.askstring("Google検索", "検索語を入力", parent=self.root)
        if not query:
            return
        url="https://www.google.com/search?"+urlencode({"q":query})
        try:
            opened=webbrowser.open(url)
            self.add(self.diagnostics, "\n[Google検索] "+query+"\n"+url+"\n")
            if not opened:
                messagebox.showinfo("Google検索", "ブラウザーを起動できませんでした。ログにURLを表示しました。")
        except Exception as exc:
            messagebox.showerror("Google検索", str(exc))

    def clipboard_read(self):
        try:
            clip=self.root.clipboard_get()
        except tk.TclError:
            messagebox.showinfo("クリップ読込", "テキストがクリップボードにありません。")
            return
        if not isinstance(clip,str) or not clip.strip():
            messagebox.showinfo("クリップ読込","クリップボードが空です。")
            return
        # Treat web/clipboard as untrusted source, display in logs, no silent training/injection.
        preview=clip[:4000]
        self.add(self.diagnostics, "\n[一時クリップ資料・未検証 / "+str(len(clip))+"文字]\n"+preview+
                 ("\n[以下省略]\n" if len(clip)>4000 else "\n"))
        self._clipboard_context=preview
        self.evidence.add(preview, 'clipboard', source_title="クリップボードからの貼り付け")
        self.refresh_evidence()
        self.add(self.conversation,
                 f"システム: クリップボードを読み込みました（{len(clip)}文字）。"
                 "一時Evidenceに登録しました（外部未検証・自動学習なし）。"
                 + ("\nシステム: 長文のため先頭4,000文字のみ登録しました。" if len(clip)>4000 else "")
                 + "\n", "system")
        self.tabs.select(self.conversation)

    def wiki_search(self):
        query=self.entry.get().strip() or simpledialog.askstring("Wikipedia検索","検索語を入力",parent=self.root)
        if not query:return
        self.add(self.diagnostics,"\n[Wikipedia検索中] "+query+"\n")
        self.tabs.select(self.diagnostics)
        def worker():
            try:
                params=urlencode({"action":"query","generator":"search","gsrsearch":query,
                                  "gsrlimit":"3","prop":"extracts","exintro":"1",
                                  "explaintext":"1","exchars":"700","format":"json"})
                url="https://ja.wikipedia.org/w/api.php?"+params
                req=Request(url,headers={"User-Agent":"LLM_CHA-ResearchGUI/0.13.58.82.2 (local educational client)"})
                with urlopen(req,timeout=12) as response:
                    payload=json.load(response)
                pages=payload.get("query",{}).get("pages",{})
                if not pages:
                    self.out.put(("wiki","[Wikipedia] 検索結果がありません。\n"))
                else:
                    lines=["[Wikipedia・外部未検証情報]"]
                    for page in sorted(pages.values(),key=lambda v:v.get("index",999)):
                        title=page.get("title","")
                        extract=page.get("extract","")
                        lines.append(title+"\n"+extract+"\n")
                    self.out.put(("wiki","\n".join(lines)+"\n"))
                    self.out.put(("wiki_evidence", (query, "\n".join(lines))))
            except Exception as exc:
                self.out.put(("wiki","[Wikipedia検索失敗] "+str(exc)+"\n"))
        threading.Thread(target=worker,daemon=True).start()

    def refresh_evidence(self):
        if not hasattr(self, "evidence_view"):
            return
        self.evidence_view.configure(state="normal")
        self.evidence_view.delete("1.0","end")
        for index, record in enumerate(self.evidence.records, 1):
            lines = [
                f"[{index}] Topic: {record['topic']}",
                f"Source: {record.get('source_title', record['source'])}",
                f"URL: {record.get('source_url') or '未設定'}",
                f"Retrieved: {record.get('retrieved_at','不明')}",
                f"Truth: {record.get('truth_state','EXTERNAL_UNVERIFIED')}",
            ]
            for attr in ("化学組成","モース硬度","屈折率","分散率","産地"):
                from temporary_evidence_v01358824 import extract_attribute
                val=extract_attribute(record["text"],attr)
                if val:
                    lines.append(f"  {attr}: {val}")
            self.evidence_view.insert("end","\n".join(lines)+"\n\n")
        self.evidence_view.configure(state="disabled")

    def status(self):
        self.add(self.diagnostics, "\n" + status_text(ROOT) + "\n")
        self.tabs.select(self.diagnostics)
        if self.proc is not None and self.proc.poll() is None:
            try:
                self.proc.stdin.write(b"/status\n")
                self.proc.stdin.flush()
            except (OSError, ValueError):
                pass

    def stop(self):
        proc = self.proc
        if proc is None:
            return
        if proc.poll() is None:
            try:
                proc.stdin.write(b"/exit\n")
                proc.stdin.flush()
            except (OSError, ValueError):
                pass
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
        for stream in (proc.stdin, proc.stdout):
            if stream:
                try:
                    stream.close()
                except OSError:
                    pass
        self.proc = None

    def restart(self):
        self.stop()
        self.add(self.conversation, "（Chatを再起動しました）\n", "system")
        self.launch()

    def close(self):
        self.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    ChatGUI(root)
    root.mainloop()
