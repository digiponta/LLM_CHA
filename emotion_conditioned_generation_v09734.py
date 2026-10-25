"""Experimental emotion-conditioned generation with conservative quality gate.

Models used in v0.9.7.32 were not trained to interpret semantic metadata.
The new prompt format is an experiment, not a validated semantic interface.
"""
import re
from emotion_aware_dialogue_v09733 import detect

BAD=("�","未学習です")
CONTRADICTIONS={
 "JOY":("残念","悲しかった","つらかった"),
 "ENJOYMENT":("残念","悲しかった","つらかった"),
 "GREETING":("残念","悲しかった"),
 "NON_SADNESS":("悲しかった","つらかった","悲しいんだね"),
 "DISAPPOINTMENT":("おめでとう","嬉しい知らせ"),
 "SADNESS":("おめでとう","それは良かった"),
 "GRATITUDE":("残念","悲しかった"),
}
def make_prompt(utterance,decision):
    return ("[EMOTION="+decision.primary+"]\n"
            "[DIALOGUE_ACT="+decision.dialogue_act+"]\n"
            "[RESPONSE_STRATEGY="+decision.strategy+"]\n"
            "人: "+utterance+"\nAI: ")

def check_response(text,decision):
    answer=str(text or "").strip()
    if not answer:return False,"empty"
    if any(x in answer for x in BAD):return False,"invalid-output"
    if len(answer)>100:return False,"too-long"
    if any(x in answer for x in CONTRADICTIONS.get(decision.primary,())):
        return False,"emotion-contradiction"
    if re.search(r"(.)\1{6,}",answer):return False,"repetitive"
    if not re.search(r"[ぁ-んァ-ヶ一-龯]",answer):return False,"no-japanese"
    # Any unrecognized strategy/emotion cannot be certified by the small gate.
    # The test must be treated as exploratory; manual review remains necessary.
    return True,"heuristic-pass"

def compare(utterance,model,tokenizer,generator,seed=42):
    decision=detect(utterance)
    if decision is None:
        return {"status":"ABSTAIN","input":utterance,"reason":"no-confident-emotion",
                "train_ready":False,"auto_promote":False}
    args={"model":model,"tokenizer":tokenizer,"max_new_tokens":48,
          "temperature":0.0,"top_k":3,"repetition_penalty":1.08,"seed":seed}
    baseline=generator(prompt="人: "+utterance+"\nAI: ",**args)
    conditioned=generator(prompt=make_prompt(utterance,decision),**args)
    from emotion_quality_gate_v09735 import assess
    passed,reason=assess(conditioned.text,decision)
    # Conservative baseline: the experimental conditional result is NOT
    # automatically published even when heuristic checks pass.
    return {"status":"DIAGNOSTIC_ONLY","input":utterance,
            "emotion":decision.snapshot(),
            "baseline":baseline.text,"conditioned":conditioned.text,
            "conditioned_gate_pass":passed,"gate_reason":reason,
            "safe_response":decision.response,
            "selected_response":decision.response,
            "selected_route":"DETERMINISTIC_EMOTION_BASELINE",
            "manual_review_required":True,
            "train_ready":False,"auto_promote":False,"persisted":False}
