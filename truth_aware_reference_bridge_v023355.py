"""v0.2.33.55 — truth-aware session reference resolution (read-only).

Requires an approved session reference, uses SemanticKnowledgeArchitecture.resolve
and the existing Truth/Provenance dispatch. Never teaches or promotes facts.
"""
from safe_reference_semantic_bridge_v023354 import SafeReferenceSemanticBridge

class TruthAwareReferenceBridge:
    def __init__(self,reference_store,semantic_architecture):
        self.references=reference_store
        self.semantic=semantic_architecture
    def lookup(self,context,subject="experiment",slot="target"):
        reference=self.references.lookup(context,subject,slot)
        if reference is None:
            return {"status":"no_approved_reference","facts":[]}
        resolved=self.semantic.resolve(f"{reference}とは")
        truth=str(resolved.truth_state or "UNVERIFIED").upper()
        state=str(resolved.state)
        action=str(resolved.action)
        answer=str(resolved.answer or "")
        provenance=resolved.provenance
        # Defensive: do not serialize arbitrary provenance objects or overstate trust.
        provenance_repr=str(provenance) if provenance is not None else ""
        safe=(truth=="TRUE" and state not in ("UNKNOWN","NON_CONCEPT")
              and bool(answer) and action not in ("REJECT","UNKNOWN","ABSTAIN"))
        return {"status":"trusted_evidence" if safe else "review_required",
                "reference":reference,"knowledge_state":state,
                "truth_state":truth,"action":action,
                "answer":answer if safe else "",
                "provenance":provenance_repr,
                "raw_answer_suppressed":not safe,
                "source":"SemanticKnowledgeArchitecture.resolve",
                "note":"A TRUE flag is only as reliable as its original evidence and provenance."}

def render_truth_reference_result(result):
    status=result["status"]
    if status=="no_approved_reference":
        return "承認済みの参照先がありません。対象を確認してください。"
    reference=result["reference"]
    if status=="trusted_evidence":
        return (f"[参照: {reference} / Truth: TRUE / 出典: {result['provenance'] or '未提示'}] "
                +result["answer"])
    return (f"参照先 {reference} の意味知識は検証待ちです。"
            f" [状態: {result['knowledge_state']} / Truth: {result['truth_state']}"
            f" / Action: {result['action']} / 出典: {result['provenance'] or '未提示'}]"
            " 未検証の回答内容は表示しません。")
