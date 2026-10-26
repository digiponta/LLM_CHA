"""v0.11.1: conservative expression resolution in front of human reconciliation.

No model-based semantic inference. A verified equivalence assertion with provenance
is required for automatic semantic normalization. Lexical NFKC equality alone can
be normalized safely as a presentation rule, not a truth judgment.
"""
from dataclasses import dataclass
from typing import Optional
from semantic_reconciliation_v0110 import ReconciliationStore, canonical_form

@dataclass(frozen=True)
class EquivalenceAssertion:
    status: str  # EQUIVALENT, DIVERGENT, UNKNOWN
    provenance_id: Optional[str] = None
    approved: bool = False
    canonical_expression: Optional[str] = None

def resolve(question, answer_a, answer_b, assertion=None, *, store=None):
    if not all(isinstance(x,str) and x.strip() for x in (question,answer_a,answer_b)):
        raise ValueError("nonempty question and answers required")
    if canonical_form(answer_a)==canonical_form(answer_b):
        return {"action":"CANONICALIZED_LEXICAL","answer":canonical_form(answer_a),
                "ticket_id":None,"factual_truth":"UNVERIFIED"}
    if assertion is None:
        assertion=EquivalenceAssertion("UNKNOWN")
    if assertion.status not in {"EQUIVALENT","DIVERGENT","UNKNOWN"}:
        raise ValueError("unrecognized equivalence status")
    if assertion.status=="EQUIVALENT":
        if (assertion.approved and isinstance(assertion.provenance_id,str)
            and assertion.provenance_id.strip() and
            isinstance(assertion.canonical_expression,str) and
            assertion.canonical_expression.strip()):
            return {"action":"CANONICALIZED_APPROVED","answer":assertion.canonical_expression,
                    "ticket_id":None,"equivalence_evidence":assertion.provenance_id,
                    "factual_truth":"UNVERIFIED"}
        # Claim of equivalence without approval is not sufficient for auto-merge.
        divergence="UNKNOWN"
    else:
        divergence=assertion.status
    store=store if store is not None else ReconciliationStore()
    ticket=store.open(question,answer_a,answer_b,divergence=divergence,
                      evidence_a={"equivalence_provenance":assertion.provenance_id},
                      evidence_b={"equivalence_provenance":assertion.provenance_id})
    return {"action":"ASK_USER","answer":None,"ticket_id":ticket["id"],
            "divergence_status":divergence,"factual_truth":"UNVERIFIED"}

def choose(store, ticket_id, decision, *, context=""):
    record=store.review(ticket_id,decision,context=context)
    return {"action":"USER_PREFERENCE_RECORDED","ticket_id":ticket_id,
            "preference":record["preferred_expression"],
            "state":record["state"],"approval_state":record["approval_state"],
            "factual_truth":record["factual_truth"]}
