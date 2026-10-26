"""Safe opt-in adapter for chat.py v0.11.9.

Only applies after existing chat truth/dispatch checks. Never writes to corpus,
knowledge approval, or checkpoint. A preference is not a fact.
"""
from pathlib import Path
from semantic_subject_preferences_v0117 import SubjectPreferenceBridge
from semantic_equivalence_router_v0111 import EquivalenceAssertion
from generation_quality_gate_v0114 import assess_generation

def get_bridge(root):
    return SubjectPreferenceBridge(root)

def memory_candidate(path, subject):
    from retrieval_first_runtime_v1012161 import resolve_subject
    return resolve_subject(Path(path),subject)

def prelookup(bridge, question, subject, context, candidate, truth_state):
    if truth_state in ("FALSE","OUTDATED","CONTESTED"):
        return None
    if not candidate.hit or not candidate.answer:
        return None
    return bridge.lookup_preference(question,subject,context,candidate.answer)

def reconcile(bridge, question, subject, context, generated, candidate, truth_state):
    if truth_state in ("FALSE","OUTDATED","CONTESTED") or not candidate.hit:
        return None
    quality=assess_generation(generated)
    if quality.status!="VALID":
        return {"action":"QUALITY_REVIEW","reasons":list(quality.reasons)}
    return bridge.compare(question,generated,candidate.answer,
                          EquivalenceAssertion("UNKNOWN",provenance_id=candidate.provenance),
                          subject=subject,context=context)

def ask_and_save(bridge, outcome, input_fn=input, print_fn=print):
    if outcome is None or outcome["action"]!="ASK_USER":
        return outcome
    print_fn(outcome["message"])
    decision=input_fn("Decision [prefer_a/prefer_b/both_contextual/neither/skip]> ").strip()
    if decision not in ("prefer_a","prefer_b","both_contextual","neither"):
        return {"action":"SKIPPED"}
    context=input_fn("Context> ").strip() if decision=="both_contextual" else ""
    try:
        return bridge.review(outcome["ticket_id"],decision,context=context)
    except ValueError as exc:
        print_fn("Review not saved: "+str(exc))
        return {"action":"SKIPPED"}
