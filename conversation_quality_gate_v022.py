"""Conservative response-quality policy for generated LLM_CHA replies.

This module does not examine, alter, or override canonical Semantic Memory
retrieval, Truth-State, or human-approved facts. It only vets raw generation.
"""
from __future__ import annotations
import re

def quality_check(question: str, answer: str, *, lexical_agreement: float,
                  semantic_agreement: float, min_lexical: float = 0.35
                  ) -> tuple[bool,str]:
    q = question.strip().rstrip("？?")
    a = answer.strip()
    if not a:
        return False, "empty generated response"
    if len(a) > 500:
        return False, "excessive response length"
    if re.search(r"^(ありがとう|助かりました|感謝します)", q):
        if not any(x in a for x in ("どういたしまして","こちらこそ","お役に立て","よかった")):
            return False, "thanks speech-act mismatch"
    if re.search(r"(疲れ|くたくた|しんどい)", q):
        if a in ("お疲れました","そうですね","いいですね"):
            return False, "fatigue response mismatch"
    if "話をして" in q or "お話して" in q:
        if len(a) < 20 or a in ("いいですね","そうですね"):
            return False, "story request not fulfilled"
    if ("どんな" in q and ("好き" in q or "本" in q)) and a in ("いいですね","そうですね"):
        return False, "question not answered"
    # Probe semantic similarity is *not* evidence of answer quality when
    # independently sampled textual outputs disagree strongly.
    if lexical_agreement < 0.15 and semantic_agreement >= 0.82:
        return False, "semantic-only rescue with very low lexical agreement"
    return True,"quality check passed"
