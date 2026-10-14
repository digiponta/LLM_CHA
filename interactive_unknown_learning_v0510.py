"""LLM_CHA v0.5.10 interactive UNKNOWN teaching; no model-weight updates.

Only explicit definitional questions open knowledge clarification. User replies
are unverified, must be confirmed, and are never marked train-ready.
"""
import json
import re
from pathlib import Path
from conversation_resource_memory_v042866 import write_json_atomic

PATTERNS=(re.compile(r"^(.{1,60}?)とは(?:何|なに|どういう|\?|？)"),re.compile(r"^(.{1,60}?)について(?:教えて|説明して)"))
YES={"はい","うん","yes","y","登録","保存"}
NO={"いいえ","いいや","no","n","キャンセル","やめる"}
def concept_from(question):
    text=question.strip().replace("　"," ")
    for pattern in PATTERNS:
        m=pattern.search(text)
        if m:
            concept=m.group(1).strip(" 、。？?")
            if concept:return concept
    return None
def classify(question,reason):
    concept=concept_from(question)
    if concept and not any(x in reason for x in ("topic grounding absent","low response agreement")):
        return "KNOWLEDGE_UNKNOWN",concept
    if concept:return "KNOWLEDGE_UNKNOWN",concept
    return "GENERATION_OR_CONTEXT_UNKNOWN",None
class UnknownTeaching:
    def __init__(self,path):
        self.path=Path(path)
        self.pending=None
    def begin(self,question,reason):
        kind,concept=classify(question,reason)
        if kind!="KNOWLEDGE_UNKNOWN":return None
        self.pending={"stage":"AWAIT_EXPLANATION","question":question,"concept":concept}
        return f"「{concept}」について十分な知識がありません。どのようなものか教えていただけますか？"
    def handle(self,answer):
        p=self.pending
        if not p:return None
        value=answer.strip()
        if p["stage"]=="AWAIT_EXPLANATION":
            if value.lower() in NO or value=="/cancel":
                self.pending=None;return "知識の登録を取り消しました。"
            if not value or value.startswith("/") or len(value)>2000:
                return "説明を文章で入力してください。中止する場合は /cancel と入力してください。"
            p["explanation"]=value
            p["stage"]="AWAIT_CONFIRMATION"
            return f"「{p['concept']}」の説明として「{value}」を未検証の知識候補に保存してよいですか？（はい／いいえ）"
        if value.lower() in NO or value=="/cancel":
            self.pending=None;return "知識の登録を取り消しました。"
        if value.lower() not in YES:
            return "保存する場合は「はい」、取り消す場合は「いいえ」と入力してください。"
        record={"version":"v0.5.10","concept":p["concept"],
                "question":p["question"],"user_explanation":p["explanation"],
                "truth_state":"USER_REPORTED_UNVERIFIED","status":"PENDING_REVIEW",
                "source":"interactive_user_confirmation","verified":False,
                "fact_promoted":False,"train_ready":False,"approved_for_sleep":False}
        self.path.parent.mkdir(parents=True,exist_ok=True)
        rows=json.loads(self.path.read_text(encoding="utf-8-sig")) if self.path.exists() else []
        if not isinstance(rows,list):raise ValueError("invalid candidate store")
        if record not in rows:rows.append(record)
        write_json_atomic(rows,self.path)
        self.pending=None
        return "未検証の知識候補として保存しました。事実確認やモデル学習はまだ行っていません。"
    def lookup(self,concept):
        if not self.path.exists():return []
        records=json.loads(self.path.read_text(encoding="utf-8-sig"))
        if not isinstance(records,list):raise ValueError("invalid candidate store")
        return [r for r in records if r.get("concept")==concept and r.get("truth_state")=="USER_REPORTED_UNVERIFIED"]
