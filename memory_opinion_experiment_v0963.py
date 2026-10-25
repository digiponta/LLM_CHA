"""v0.9.6.3 evidence-backed, bounded interpretation candidate.

This is a deterministic experimental interpretation, NOT a model-generated answer.
Quality gate result can be compared to the existing safe baseline.
"""
from grounded_generation_gate_v096 import compare

def evaluate_memory_opinion(topic,evidence,baseline):
    if not evidence:
        return {"status":"KEEP_BASELINE","selected":baseline,"reason":"NO_EVIDENCE"}
    excerpt=evidence[0]["text"] if isinstance(evidence[0],dict) else str(evidence[0])
    candidate=(f"{topic}については、長門コーパスの原文「{excerpt}」を手掛かりに検討できる。"
               "これは未検証の考察なので、一般的な事実とは分けて扱いたい。")
    result=compare(baseline,candidate,"貴方はどう思う？",topic,[excerpt])
    result["candidate_origin"]="DETERMINISTIC_TEMPLATE_NOT_LLM"
    result["subtopic"]=evidence[0].get("subtopic") if isinstance(evidence[0],dict) else None
    return result
