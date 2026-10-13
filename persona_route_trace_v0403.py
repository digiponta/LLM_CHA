"""v0.4.3 read-only Persona routing trace, no decision overrides."""
from __future__ import annotations
from persona_routing_v0374 import ranked_persona_reply

def diagnose(source, dispatch_action, dispatch_state, dispatch_focus,
             truth_runtime_status=None, force_verification=False):
    focus=(dispatch_focus or "").strip()
    try:
        _,evidence=ranked_persona_reply(source,focus) if focus else (None,[])
        evidence_count=len(evidence)
        evidence_lines=[x.line for x in evidence]
        retrieval_error=None
    except (OSError,ValueError) as exc:
        evidence_count=0
        evidence_lines=[]
        retrieval_error=type(exc).__name__
    gate_block=truth_runtime_status=="BLOCK"
    rescue_condition=(dispatch_action=="BLOCK" and
                      dispatch_state=="RAW_CORPUS_ONLY" and
                      not force_verification and not gate_block)
    reasons=[]
    if dispatch_action!="BLOCK":reasons.append("action_not_BLOCK")
    if dispatch_state!="RAW_CORPUS_ONLY":reasons.append("state_not_RAW_CORPUS_ONLY")
    if force_verification:reasons.append("internalized_verification_override")
    if gate_block:reasons.append("truth_runtime_BLOCK")
    if not focus:reasons.append("empty_dispatch_focus")
    if not evidence_count:reasons.append("no_ranked_persona_evidence")
    return {"version":"v0.4.3","focus":focus,
            "dispatch_action":dispatch_action,"dispatch_state":dispatch_state,
            "truth_runtime_status":truth_runtime_status or "UNSPECIFIED",
            "forced_verification":bool(force_verification),
            "persona_rescue_condition":rescue_condition,
            "persona_rescue_hit_possible":bool(rescue_condition and focus and evidence_count),
            "ranked_evidence_count_max_2":evidence_count,
            "evidence_lines":evidence_lines,
            "retrieval_error":retrieval_error,
            "non_hit_reasons":reasons,
            "truth_gate_modified":False,"route_modified":False}
