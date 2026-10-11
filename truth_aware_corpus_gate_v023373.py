"""v0.2.33.73: strict truth policy for direct corpus-memory answers.

A retrieval hit establishes *text availability*, not truth. Only an explicit
TRUE truth record may enter the direct factual-answer path. UNVERIFIED and
CONTESTED fail closed; FALSE and OUTDATED continue to existing correction policy.
This gate is conservative but does not independently authenticate TRUE records.
"""
VALID_STATES=frozenset(("TRUE","FALSE","UNVERIFIED","CONTESTED","OUTDATED"))
def corpus_answer_decision(state,hit):
    if state not in VALID_STATES:raise ValueError("invalid_truth_state")
    if not isinstance(hit,bool):raise ValueError("invalid_hit")
    if not hit:return "MISS"
    if state=="TRUE":return "ALLOW_VERIFIED_STATE"
    if state in ("UNVERIFIED","CONTESTED"):return "BLOCK_UNVERIFIED_CORPUS"
    return "DEFER_TRUTH_CORRECTION"
