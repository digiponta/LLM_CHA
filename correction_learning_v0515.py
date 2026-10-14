"""v0.5.15: one-shot correction dialogue after explicit negative feedback.

A correction is a separate unverified candidate linked to the old candidate.
The original stays CONTESTED. No automatic promotion, deletion or training.
"""
from usage_confidence_v0513 import get
from conversation_resource_memory_v042866 import write_json_atomic

class CorrectionSession:
    def __init__(self):
        self.pending=None

    def start(self,path,source_id):
        _,old=get(path,source_id)
        if old.get("operational_status")!="CONTESTED":
            raise ValueError("source must be contested")
        self.pending={"stage":"EXPLANATION","source_id":source_id,
                      "concept":old["concept"]}
        return "どの部分が間違っていますか？ 正しい説明を教えてください。（中止: /cancel）"

    def respond(self,path,message):
        state=self.pending
        if state is None:return None
        answer=message.strip()
        if answer=="/cancel" or answer=="いいえ" and state["stage"]=="CONFIRM":
            self.pending=None
            return "訂正候補の保存を取り消しました。"
        if state["stage"]=="EXPLANATION":
            if not answer or answer.startswith("/") or len(answer)>2000:
                return "訂正説明を文章で入力してください。（中止: /cancel）"
            state["explanation"]=answer
            state["stage"]="CONFIRM"
            return f"訂正説明「{answer}」を未検証候補として保存してよいですか？（はい／いいえ）"
        if answer!="はい":
            return "保存する場合は「はい」、取り消す場合は「いいえ」と入力してください。"
        data,old=get(path,state["source_id"])
        if old["concept"]!=state["concept"] or old.get("operational_status")!="CONTESTED":
            raise ValueError("source changed during correction")
        new={"version":"v0.5.15","concept":state["concept"],
             "question":old.get("question",""),
             "user_explanation":state["explanation"],
             "truth_state":"USER_REPORTED_UNVERIFIED",
             "status":"CORRECTION_PENDING_REVIEW",
             "operational_status":"PROVISIONAL",
             "source":"user_correction",
             "corrects_candidate_id":state["source_id"],
             "verified":False,"fact_promoted":False,
             "train_ready":False,"approved_for_sleep":False}
        data.append(new)
        write_json_atomic(data,path)
        self.pending=None
        return f"訂正候補 ID {len(data)} を保存しました。元の候補はCONTESTEDのままです。"
