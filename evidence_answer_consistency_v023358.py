"""v0.2.33.58 Evidence-to-Answer Consistency Validation.

Conservative deterministic exact proposition check. A provenance metadata label
alone does NOT establish factual correctness. Only explicit evidence text that
exactly supports the candidate answer can pass. Unsupported elaboration blocks.
This is a structural support check, not independent external fact verification.
"""
import unicodedata
from evidence_grounded_reference_v023357 import EvidenceGroundedReferenceBridge

def canonical(text):
    return unicodedata.normalize("NFKC",str(text or "")).strip().rstrip("。．.!！ \t\r\n")

def supporting_evidence(result):
    provenance=getattr(result,"provenance",None)
    evidence=str(getattr(provenance,"evidence","") or "")
    answer=str(getattr(result,"answer","") or "")
    if not answer.strip() or not evidence.strip():
        return False,"missing_evidence_text"
    # Compare whole normalized statements, not substring containment.
    # This intentionally refuses summaries, paraphrases and extra clauses.
    if canonical(evidence)!=canonical(answer):
        return False,"answer_not_exactly_supported"
    return True,"exact_statement_match"

class ConsistencyReferenceBridge(EvidenceGroundedReferenceBridge):
    def lookup(self,context):
        reference=self.references.lookup(context,"experiment","target")
        if reference is None:return {"status":"no_approved_reference"}
        mapping=self.mappings.lookup(context,reference)
        if mapping is None:return {"status":"no_approved_mapping","reference":reference}
        result=self.semantic.resolve(f"{mapping['concept']}とは")
        from evidence_grounded_reference_v023357 import evidence_gate
        allowed,reason=evidence_gate(result)
        if allowed:allowed,reason=supporting_evidence(result)
        p=getattr(result,"provenance",None)
        return {"status":"consistent_evidence" if allowed else "consistency_blocked",
                "reason":reason,"reference":reference,"concept":mapping["concept"],
                "mapping_provenance":mapping["mapping_provenance"],
                "knowledge_state":str(result.state),
                "truth_state":str(result.truth_state or "UNVERIFIED"),
                "provenance_source":str(getattr(p,"source","") or ""),
                "answer":str(result.answer) if allowed else ""}

def render_consistency(r):
    if r["status"]=="no_approved_reference":return "承認済み参照がありません。"
    if r["status"]=="no_approved_mapping":return "承認済みの参照と概念の対応関係がありません。"
    head=f"[参照 {r['reference']} → {r['concept']}; Truth={r['truth_state']}; source={r['provenance_source']}]"
    if r["status"]=="consistent_evidence":
        return head+" 証拠と完全一致した回答候補: "+r["answer"]
    return head+" 回答保留（"+r["reason"]+"）。"
