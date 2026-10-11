"""v0.2.33.54: read-only bridge from an approved session reference to atomic propositions.

No alias inference, no writes to Semantic Memory, no /sleep.
Only exact subject match is accepted; candidate expiry is checked by store.lookup.
"""
from pathlib import Path
from semantic_proposition_v1090 import load_propositions

class SafeReferenceSemanticBridge:
    def __init__(self,reference_store,proposition_path):
        self.references=reference_store
        self.proposition_path=Path(proposition_path)

    def lookup(self,context,subject="experiment",slot="target"):
        reference=self.references.lookup(context,subject,slot)
        if reference is None:
            return {"status":"no_approved_reference","context":context,"facts":[]}
        # No mapping between cursor / semantic_memory and a distinct knowledge
        # subject is guessed. Only exact subject matches are retrieved.
        records=[p for p in load_propositions(self.proposition_path) if p.subject==reference]
        if not records:
            return {"status":"no_semantic_evidence","context":context,
                    "reference":reference,"facts":[],"source":"atomic_propositions_read_only"}
        return {"status":"evidence_found","context":context,"reference":reference,
                "facts":[{"subject":p.subject,"value":p.value} for p in records],
                "source":"atomic_propositions_read_only",
                "warning":"Source records are not automatically verified for truth or freshness."}

def render_safe_semantic_result(result):
    state=result["status"]
    if state=="no_approved_reference":
        return "承認済みの参照先がありません。対象を確認してください。"
    if state=="no_semantic_evidence":
        return f"参照先 {result['reference']} に一致する意味命題は見つかりませんでした。知識として自動登録はしません。"
    if state=="evidence_found":
        text=" / ".join(f"{r['subject']}は、{r['value']}である。" for r in result["facts"])
        return f"[原子的意味命題・未検証の可能性] {text}"
    raise ValueError(f"Unsupported semantic bridge status: {state}")
