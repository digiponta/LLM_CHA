"""v0.7.13 candidate-aware response validation, preserving unverified state.

Exact answer matching is a consistency check, not a factual truth check.
Only an exact PENDING question may authorize the matching response.
"""
from experimental_quality_gate_v0711 import quality_gate

def validate_candidate_response(question, generated, record):
    if not isinstance(record, dict) or record.get("status") != "PENDING":
        return {"accepted":False,"reason":"not_pending"}
    if str(question).strip() != str(record.get("question","")).strip():
        return {"accepted":False,"reason":"question_mismatch"}
    expected=str(record.get("answer","")).strip()
    actual=str(generated or "").strip()
    if not actual:
        return {"accepted":False,"reason":"empty"}
    if len(actual)>450:
        return {"accepted":False,"reason":"too_long"}
    if actual == expected:
        return {"accepted":True,"reason":"candidate_exact_consistency"}
    passed, reason=quality_gate(question,actual)
    # A nonmatching generated answer is NOT supported by this candidate,
    # even when the generic textual heuristic considers it fluent.
    return {"accepted":False,"reason":"candidate_answer_mismatch" if passed else reason}

def candidate_answer_fallback(question, backend, record):
    generated=backend(question)
    verdict=validate_candidate_response(question,generated,record)
    if not verdict["accepted"]:
        return {"route":"EXPERIMENTAL_REJECTED","answer":None,
                "truth_state":"UNKNOWN","reason":verdict["reason"],
                "auto_promote":False,"candidate_id":record["id"],
                "source_id":record["source_id"]}
    return {"route":"EXPERIMENTAL_FALLBACK",
            "answer":"【未承認・実験的回答】"+str(generated).strip(),
            "truth_state":"EXPERIMENTAL_UNVERIFIED",
            "reason":verdict["reason"],"auto_promote":False,
            "candidate_id":record["id"],"source_id":record["source_id"]}
