"""Deterministic v0.2.6 diagnostic heuristics (not an LLM judge)."""
from __future__ import annotations
GENERIC = frozenset({"そうですね","そう","はい","いいですね","なるほど","わかりました","了解です","こんにちは","お願いしますよ"})
CONTEXT_CUES = ("続けて","その話","それについて","さっきの","もう少し","詳しく")
def classify_quality(question:str, answer:str):
    q=question.strip().rstrip("。!?！？ ")
    a=answer.strip().rstrip("。!?！？ ")
    generic=a in GENERIC
    context_required=any(s in q for s in CONTEXT_CUES)
    short=len(a)<8
    reason=("generic reply to context request" if generic and context_required else
            "unfulfilled context request" if context_required and short else
            "generic non-answer" if generic else "no obvious diagnostic issue")
    return {"generic":generic,"context_required":context_required,"short":short,
            "flag":generic and context_required or context_required and short,
            "reason":reason}
def prompt_debug(prompt:str, selected_history:int, extra_user_context:bool):
    return (f"[prompt-inspection selected_history={selected_history}, "
            f"transient_context={extra_user_context}, chars={len(prompt)}]\n"
            + "----- model prompt begin -----\n" + prompt
            + "\n----- model prompt end -----")
