"""v0.7.12 Candidate-aware gate review fallback (fail closed)."""
from dual_semantic_memory_v071 import DualMemory
from candidate_response_validation_v0713 import candidate_answer_fallback

def candidate_match(memory, question):
    question = str(question).strip()
    if not question:
        return None
    matches = [r for r in memory.candidates()
               if r["status"] == "PENDING" and r["question"].strip() == question]
    if len(matches) != 1:
        return None
    return matches[0]

def gate_review_fallback(question, approved_path, candidate_path, backend, *, resolution, enabled):
    if not enabled or backend is None or resolution != "GATE_REVIEW":
        return None
    match = candidate_match(DualMemory(approved_path, candidate_path), question)
    if match is None:
        return None
    return candidate_answer_fallback(question, backend, match)
