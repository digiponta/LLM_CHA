"""Narrow opt-in Theme RSE route used only after existing chat.py retrieval gates.

Only conversation invitation and current-activity intents are covered.
Other intents return None, preserving existing LLM behavior.
"""
from rse_semantic_theme_v013588312 import semantic_features
from rse_candidate_lifecycle_v013588322 import resolve

def decide_live_route(question,store):
    features=semantic_features(question)
    intent=features["intent"]
    if intent not in {"INVITE_CONVERSATION","CURRENT_ACTIVITY"}:
        return None
    # Approval lifecycle and Theme/Intent/Time/Relation matcher remain
    # authoritative. Do not accept an unapproved or revoked candidate.
    try:
        result=resolve(store,question)
    except (ValueError, OSError, KeyError, TypeError):
        return {"answer":"未学習です","route":"RSE_STORE_ERROR_EXPERIMENTAL",
                "candidate_id":None}
    action=result["decision"]["action"]
    if action=="SELECT_RSE":
        return {"answer":result["decision"]["answer"],
                "route":"RSE_APPROVED_EXPERIMENTAL",
                "candidate_id":result["rse"].get("candidate_id")}
    if action=="ABSTAIN":
        return {"answer":"未学習です","route":"RSE_UNLEARNED_EXPERIMENTAL",
                "candidate_id":None}
    # Fail closed on policy ambiguity; never print a generic LLM
    # completion as though it had passed the relevance gate.
    return {"answer":"未学習です","route":"RSE_REVIEW_REQUIRED_EXPERIMENTAL",
            "candidate_id":None}
