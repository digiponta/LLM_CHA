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
from menu_evidence_v013588215 import retrieve_menu, format_menu
from product_dialogue_v013588217 import ProductDialogue
from dialogue_intent_gate_v013588218 import DialogueIntentGate
from general_dialogue_intent_v013588219 import GeneralDialogueIntentContext
from episodic_context_v013588220 import EpisodeContext
from episodic_retrieval_v013588222 import retrieve_episodes, natural_summary
from episodic_memory_gate_v013588223 import EpisodicMemoryGate
from approved_episode_retrieval_v013588224 import ApprovedEpisodeRetriever
from unified_episode_retrieval_v013588225 import UnifiedEpisodeRetriever
from topic_answer_context_v013588226 import TopicAnswerContext
from grounded_elaboration_v013588227 import elaborate_from_wikipedia
from evidence_conditioned_generation_v013588228 import retrieve_evidence,conditioned_prompt,final_answer
from generation_diagnostics_v013588230 import GenerationDiagnostics
from generation_attempt_tracker_v013588231 import AttemptTracker
from llm_input_channel_v013588233 import send_one_line, normalize_one_line
from evidence_aware_route_v013588236 import encode_request
from evidence_candidate_analysis_v013588237 import analyze
from rejected_answer_repair_v013588239 import RepairQueue, REJECTED
from response_correlation_v013588235 import response_action
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
        self.product_dialogue = ProductDialogue()
        self.intent_gate = DialogueIntentGate()
        self.general_intent = GeneralDialogueIntentContext()
        self.episodes = EpisodeContext()
        self.episode_gate = EpisodicMemoryGate(ROOT / 'data' / 'approved_episodic_memory.json')
        self.last_staged_episode_id = None
        self.approved_retriever = ApprovedEpisodeRetriever(self.episode_gate)
        self.unified_retriever = UnifiedEpisodeRetriever(self.episodes,self.episode_gate)
        self.dialogue_context = UnifiedDialogueContext()
        self.topic_answers = TopicAnswerContext()
        self.pending_auto_wiki_question = None
        self.pending_grounded_prompts = {}
        self.candidate_analyses = []
        self.repair_queue = RepairQueue(ROOT / "data" / "rejected_answer_repairs.jsonl")
        self.generation_diagnostics = GenerationDiagnostics()
        self.attempt_tracker = AttemptTracker()
        self.pending_attempt_ids = []
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
            if response_action(question,answer)=="SUPPRESS_UNCORRELATED":
                # chat.py may emit an additional unscheduled AI> line.
                # It must never be rendered as a second answer to the same user turn.
                self.add(self.diagnostics,"[Uncorrelated AI suppressed] "+answer[:160]+"\n")
                return
            if question in self.pending_grounded_prompts:
                evidence=self.pending_grounded_prompts.pop(question)
                result=final_answer(answer,evidence)
                if result["gate"] in REJECTED:
                    try:
                        repair=self.repair_queue.stage(evidence.get("topic",""),answer,evidence,result["gate"])
                        self.add(self.diagnostics,"[Repair Staged] "+repair["id"]+" / "+result["gate"]+"\n")
                    except (ValueError,OSError) as exc:
                        self.add(self.diagnostics,"[Repair Stage Failure] "+str(exc)+"\n")
                analysis=analyze(answer,evidence,result["gate"])
                self.candidate_analyses.append(analysis)
                self.add(self.diagnostics,"[Candidate Analysis] "+json.dumps({
                    "gate":analysis["gate"],
                    "sentences":analysis["candidate_sentences"]
                },ensure_ascii=False)+"\n")
                if self.pending_attempt_ids:
                    self.attempt_tracker.transition(self.pending_attempt_ids.pop(0),"COMPLETED",result["gate"])
                self.generation_diagnostics.record(result["gate"],evidence.get("status",""),evidence.get("topic",""),answer,result["answer"])
                self.add(self.diagnostics,"[Evidence Gate] "+result["gate"]+
                         " / candidate_chars="+str(len(answer))+
                         " / candidate_preview="+repr(answer[:100])+"\n")
                self.add(self.conversation,"AI: "+result["answer"]+"\n","assistant")
            elif question and is_unknown_answer(answer):
                self.add(self.conversation,"システム: 未学習のためWikipediaを検索しています。\n","system")
                self.pending_auto_wiki_question = question
                self.auto_wiki(question)
            else:
                self.topic_answers.record(question,answer,"LLM_RUNTIME")
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
                rendered=format_result(data)
                if data.get("status") in ("HIT","FOUND","OK","SUCCESS"):
                    self.topic_answers.record(self.pending_auto_wiki_question or "",rendered,"WIKIPEDIA_UNVERIFIED")
                self.pending_auto_wiki_question=None
                self.add(self.conversation,rendered,"assistant")
                self.wiki_inflight=False
            elif kind == "conditioned_evidence":
                evidence=data
                attempt_id=evidence.get("_attempt_id")
                if evidence.get("status")!="EVIDENCE":
                    result=final_answer("",evidence)
                    if attempt_id:self.attempt_tracker.transition(attempt_id,"COMPLETED",result["gate"])
                    self.generation_diagnostics.record(result["gate"],evidence.get("status",""),evidence.get("topic",""),"",result["answer"])
                    self.add(self.conversation,"AI: "+result["answer"]+"\n","assistant")
                elif self.proc is None or self.proc.poll() is not None:
                    result=final_answer("",evidence)
                    if attempt_id:
                        self.attempt_tracker.annotate(attempt_id,failure_reason="NO_MODEL",process_alive=False)
                        self.attempt_tracker.transition(attempt_id,"FAILED","NO_MODEL")
                    self.generation_diagnostics.record("NO_MODEL",evidence.get("status",""),evidence.get("topic",""),"",result["answer"])
                    self.add(self.conversation,"AI: "+result["answer"]+"\n","assistant")
                else:
                    prompt=encode_request(evidence["topic"],evidence["excerpt"])
                    if attempt_id:self.attempt_tracker.annotate(attempt_id,prompt_chars=len(prompt),process_alive=True)
                    try:
                        # Register only after validation and successful send.
                        send_one_line(self.proc,prompt)
                        self.pending_grounded_prompts[prompt]=evidence
                        if attempt_id:
                            self.attempt_tracker.transition(attempt_id,"WAITING_LLM")
                            self.pending_attempt_ids.append(attempt_id)
                        self.pending_llm_questions.put(prompt)
                        self.add(self.diagnostics,"[Evidence-Aware Candidate Route] "+evidence["query"]+"\n")
                    except (OSError,ValueError,RuntimeError) as exc:
                        reason=str(exc) if str(exc) in ("PROMPT_MULTILINE","STDIN_UNAVAILABLE","PROCESS_NOT_RUNNING") else "SEND_FAILED"
                        if attempt_id:
                            self.attempt_tracker.annotate(attempt_id,failure_reason=reason,exception_type=type(exc).__name__,process_alive=self.proc is not None and self.proc.poll() is None)
                            self.attempt_tracker.transition(attempt_id,"FAILED",reason)
                        self.add(self.diagnostics,"[Generation Send Failure] "+type(exc).__name__+": "+str(exc)+"\n")
                        self.add(self.conversation,"AI: "+final_answer("",evidence)["answer"]+"\n","assistant")
            elif kind == "topic_elaboration":
                self.add(self.diagnostics,"[話題詳細化] "+data["topic"]+" / "+str(data["status"])+"\n")
                self.add(self.conversation,"AI: "+data["answer"]+"\n","assistant")
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
        if text.startswith("/repair"):
            self.add(self.conversation,"あなた: "+text+"\n","user")
            parts=text.split(" ",3)
            try:
                action=parts[1] if len(parts)>1 else "help"
                if action=="list":
                    items=self.repair_queue.list()
                    reply=json.dumps([{"id":x["id"],"question":x["question"],"gate":x["gate"],"state":x["state"]} for x in items[-10:]],ensure_ascii=False,indent=2)
                elif action=="propose" and len(parts)==4:
                    row=self.repair_queue.propose(parts[2],parts[3])
                    reply="正解候補を審査待ちにしました: "+row["id"]
                elif action=="approve" and len(parts)==3:
                    row=self.repair_queue.approve(parts[2])
                    reply="明示承認済み（未学習）: "+row["id"]
                elif action=="reject" and len(parts)==3:
                    row=self.repair_queue.reject(parts[2])
                    reply="修復候補を却下しました: "+row["id"]
                elif action=="export":
                    n=self.repair_queue.export_approved(ROOT / "results" / "repair_training_candidates_v013588239.json")
                    reply="実験用候補を出力しました: "+str(n)+"件。自動学習はしません。"
                else:
                    reply="/repair list | /repair propose ID 正解文 | /repair approve ID | /repair reject ID | /repair export"
            except (ValueError,KeyError,OSError) as exc:
                reply="Repair操作失敗: "+str(exc)
            self.add(self.conversation,"システム: "+reply+"\n","system")
            self.entry.delete(0,"end")
            return
        if text=="/gencandidates":
            self.add(self.conversation,"あなた: "+text+"\n","user")
            if not self.candidate_analyses:
                response="分析対象の生成候補はありません。"
            else:
                response=json.dumps(self.candidate_analyses[-3:],ensure_ascii=False,indent=2)
            self.add(self.conversation,"システム: "+response+"\n","system")
            self.entry.delete(0,"end")
            return
        if text in ("/genstats","/genstats reset","/gencompare"):
            if text=="/genstats reset":
                self.generation_diagnostics.reset()
                self.candidate_analyses.clear()
                self.attempt_tracker.reset()
                self.pending_attempt_ids.clear()
                response="生成診断のセッション内集計を初期化しました。"
            else:
                data=(self.generation_diagnostics.comparison() if text=="/gencompare"
                      else self.generation_diagnostics.report())
                data["lifecycle"]=self.attempt_tracker.report()
                response=json.dumps(data,ensure_ascii=False,indent=2)
            self.add(self.conversation,"あなた: "+text+"\n","user")
            self.add(self.conversation,"システム: "+response+"\n","system")
            self.entry.delete(0,"end")
            return
        # Explicit approval: never save a user episode silently.
        if text.startswith("/episode"):
            parts=text.split()
            action=parts[1] if len(parts)>1 else "help"
            self.add(self.conversation,"あなた: "+text+"\n","user")
            try:
                if action=="stage":
                    if not self.episodes.active:
                        reply="保存候補のEpisodeがありません。"
                    else:
                        item=self.episode_gate.stage(self.episodes.active)
                        self.last_staged_episode_id=item["episode_id"]
                        reply=("Episodeを承認待ちにしました。ID: "+item["episode_id"]+
                               "\n対象: "+item["subject"]+
                               "\n保存する場合は /episode approve "+item["episode_id"])
                elif action=="approve" and len(parts)==3:
                    record=self.episode_gate.approve(parts[2])
                    reply="明示承認によりローカルのEpisodeストアへ保存しました: "+record["episode_id"]
                elif action=="reject" and len(parts)==3:
                    self.episode_gate.reject(parts[2])
                    reply="承認待ちEpisodeを破棄しました。"
                elif action=="list":
                    entries=self.episode_gate.list_approved()
                    reply=("承認済みEpisode "+str(len(entries))+"件\n"+
                           "\n".join(x["episode_id"]+" : "+x["subject"] for x in entries)) if entries else "承認済みEpisodeはありません。"
                elif action=="revoke" and len(parts)==3:
                    self.episode_gate.revoke(parts[2])
                    reply="指定した承認済みEpisodeをローカルストアから削除しました。"
                else:
                    reply=("使い方: /episode stage、/episode approve <ID>、"+
                           "/episode reject <ID>、/episode list、/episode revoke <ID>。"+
                           "\n承認済みのEpisodeはLLMの重みや従来Semantic Memoryには自動反映されません。")
            except (OSError,ValueError,KeyError) as exc:
                reply="Episode操作は完了しませんでした: "+str(exc)
            self.add(self.conversation,"システム: "+reply+"\n","system")
            self.entry.delete(0,"end")
            return
        # Explicit return and elaboration must precede external-search fallback.
        topic_action=self.topic_answers.navigate(text)
        if topic_action is not None:
            state,topic,reply=topic_action
            if state=="ELABORATE":
                self.add(self.conversation,"あなた: "+text+"\n","user")
                self.add(self.conversation,"システム: 「"+topic+"」の根拠資料を確認しています。\n","system")
                attempt_id=self.attempt_tracker.start(topic)
                self.add(self.diagnostics,"[Generation Attempt STARTED] "+attempt_id+" / "+topic+"\n")
                def topic_worker(current_topic=topic,current_attempt=attempt_id):
                    try:
                        previous=self.topic_answers.history.get(current_topic)
                        result=retrieve_evidence(current_topic,previous.answer if previous else "")
                    except Exception:
                        result={"topic":current_topic,"status":"ERROR",
                                "answer":"資料の取得に失敗しました。前回のLLM回答を根拠なく詳述することは避けます。"}
                    result["_attempt_id"]=current_attempt
                    self.out.put(("conditioned_evidence",result))
                threading.Thread(target=topic_worker,daemon=True).start()
                self.entry.delete(0,"end")
                return
            if state=="RETURNED":
                self.dialogue_context.switch(topic)
                self.evidence.set_topic(topic)
                self.preference_context.set_topic(topic)
            self.add(self.conversation,"あなた: "+text+"\n","user")
            self.add(self.conversation,"AI: "+reply+"\n","assistant")
            self.entry.delete(0,"end")
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
        try:
            unified_answer=self.unified_retriever.answer(text)
        except (OSError,ValueError) as exc:
            unified_answer="Episode記録を読み込めませんでした: "+str(exc)
        if unified_answer is not None:
            self.add(self.conversation,"あなた: "+text+"\n","user")
            self.add(self.conversation,"AI: "+unified_answer+"\n","assistant")
            self.entry.delete(0,"end")
            return
        if re.fullmatch(r"(?:さっきの|先ほどの)?(?:感想|印象)(?:は|を教えて)?[？?]?",text):
            active=self.episodes.active
            summary=(natural_summary(active) if active is not None and active.topic==self.evidence.topic else None) or self.episodes.summary(self.evidence.topic)
            self.add(self.conversation,"あなた: "+text+"\n","user")
            self.add(self.conversation,"AI: "+(summary or "この話題で記録した感想はまだありません。")+"\n","assistant")
            self.entry.delete(0,"end")
            return
        # Explicit self-reported episode details are recorded in session only.
        if not re.search(r"(?:飲んだ|飲みました|食べた|食べました|好き)",text):
            self.episodes.observe(text,self.evidence.topic)
        general_reply=self.general_intent.respond(text,self.evidence.topic)
        if general_reply is not None:
            self.intent_gate.awaiting_taste=False
            self.add(self.conversation,"あなた: "+text+"\n","user")
            self.add(self.conversation,"AI: "+general_reply+"\n","assistant")
            self.entry.delete(0,"end")
            return
        short_reply=self.intent_gate.respond(text)
        if short_reply is not None:
            self.add(self.conversation,"あなた: "+text+"\n","user")
            self.add(self.conversation,"AI: "+short_reply+"\n","assistant")
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
            menu_result=retrieve_menu(self.evidence,text)
            if menu_result is not None and menu_result["status"]=="MENU":
                self.add(self.conversation,"あなた: "+text+"\n","user")
                self.add(self.conversation,"AI: "+format_menu(menu_result)+"\n","assistant")
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
            product_reply=self.product_dialogue.respond(text,self.evidence.records,self.evidence.topic)
            if product_reply is not None:
                self.add(self.conversation,"あなた: "+text+"\n","user")
                self.intent_gate.observe_assistant(product_reply)
                self.general_intent.observe(product_reply,self.product_dialogue.last_product,self.evidence.topic)
                self.episodes.start(self.evidence.topic,self.product_dialogue.last_product,("飲んだ" if re.search(r"飲んだ|飲みました",text) else "食べた" if re.search(r"食べた|食べました",text) else "好み" if re.search(r"好き",text) else "発言"))
                self.add(self.conversation,"AI: "+product_reply+"\n","assistant")
                self.entry.delete(0,"end")
                return
        if intent is None:
            preference_reply=self.preference_context.respond(text)
            if preference_reply is not None:
                self.add(self.conversation,"あなた: "+text+"\n","user")
                self.general_intent.observe(preference_reply,self.preference_context.topic,self.evidence.topic)
                self.episodes.start(self.evidence.topic,self.preference_context.topic,"好み")
                self.episodes.observe(text,self.evidence.topic)
                self.add(self.conversation,"AI: "+preference_reply+"\n","assistant")
                self.entry.delete(0,"end")
                return
        # Self-reported liking does not require catalog confirmation.
        if intent is None:
            match=re.fullmatch(r"(.{2,70}?)(?:も|が)?好き(?:です|だ)?[。！!]*",text)
            if match:
                subject=match.group(1).strip()
                if subject:
                    reply=subject+"も好きなんだね。どんなところが気に入っているの？"
                    self.episodes.start(self.evidence.topic or subject,subject,"好み")
                    self.episodes.observe(text,self.evidence.topic or subject)
                    self.general_intent.observe(reply,subject,self.evidence.topic)
                    self.add(self.conversation,"あなた: "+text+"\n","user")
                    self.add(self.conversation,"AI: "+reply+"\n","assistant")
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
                self.general_intent.clear()
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
        self.topic_answers.note_question(text)
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
