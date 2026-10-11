"""v0.2.33.57: provenance-grounded answer gate.

Opt-in bridge: explicit reference & mapping + semantic resolution + provenance.
Rejects unverifiable, stale, conflicting or missing sources; no model training.
"""
from dataclasses import dataclass
from pathlib import Path
from verified_reference_concept_v023356 import VerifiedConceptMapping

APPROVED_ACTIONS=frozenset({"ANSWER","RESPOND","ACCEPT"})
BLOCKED_STATES=frozenset({"UNKNOWN","NON_CONCEPT","RAW_CORPUS_ONLY","CONTESTED","OUTDATED"})
BLOCKED_SOURCES=frozenset({"","none","unknown","unverified"})

def evidence_gate(result):
    truth=str(getattr(result,"truth_state","") or "UNVERIFIED").upper()
    state=str(getattr(result,"state","") or "UNKNOWN").upper()
    action=str(getattr(result,"action","") or "BLOCK").upper()
    answer=str(getattr(result,"answer","") or "")
    provenance=getattr(result,"provenance",None)
    source=str(getattr(provenance,"source","") or "").lower()
    evidence=str(getattr(provenance,"evidence","") or "")
    origin=str(getattr(provenance,"origin","") or "")
    if truth!="TRUE":return False,"truth_not_true"
    if state in BLOCKED_STATES:return False,"knowledge_not_validated"
    if action not in APPROVED_ACTIONS:return False,"dispatcher_not_allowlisted"
    if not answer.strip():return False,"empty_answer"
    if source in BLOCKED_SOURCES or not (evidence.strip() or origin.strip()):
        return False,"no_grounded_provenance"
    if str(getattr(provenance,"retrieval_priority","")).strip()=="60" and source=="none":
        return False,"unverified_source"
    return True,"supported_by_metadata"

class EvidenceGroundedReferenceBridge:
    def __init__(self,references,mappings,semantic):
        self.references=references;self.mappings=mappings;self.semantic=semantic
    def lookup(self,context):
        reference=self.references.lookup(context,"experiment","target")
        if reference is None:return {"status":"no_approved_reference"}
        mapping=self.mappings.lookup(context,reference)
        if mapping is None:return {"status":"no_approved_mapping","reference":reference}
        result=self.semantic.resolve(f"{mapping['concept']}とは")
        passed,reason=evidence_gate(result)
        provenance=getattr(result,"provenance",None)
        return {"status":"evidence_allowed" if passed else "evidence_blocked",
                "reason":reason,"reference":reference,"concept":mapping["concept"],
                "mapping_provenance":mapping["mapping_provenance"],
                "knowledge_state":str(result.state),"truth_state":str(result.truth_state or "UNVERIFIED"),
                "action":str(result.action),
                "provenance_source":str(getattr(provenance,"source","") or ""),
                "answer":str(result.answer) if passed else ""}

def render_grounded_result(r):
    if r["status"]=="no_approved_reference":return "承認済み参照はありません。"
    if r["status"]=="no_approved_mapping":return f"参照先 {r['reference']} に承認済み概念対応がありません。"
    head=(f"[参照 {r['reference']} → {r['concept']}; Knowledge={r['knowledge_state']}; "
          f"Truth={r['truth_state']}; source={r['provenance_source']}]")
    if r["status"]=="evidence_allowed":
        return head+" 証拠メタデータに基づく回答候補: "+r["answer"]
    return head+" 回答保留（"+r["reason"]+"）。"
