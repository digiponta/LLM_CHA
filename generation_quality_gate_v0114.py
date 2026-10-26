"""v0.11.4 conservative generation-quality gate.

This gate detects clearly invalid text and decoder token-cap termination.
It never declares semantic equivalence or validates factual truth.
"""
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class QualityResult:
    status: str
    reasons: tuple[str,...]

def assess_generation(generated):
    text=generated if isinstance(generated,str) else getattr(generated,"text","")
    termination=None if isinstance(generated,str) else getattr(generated,"termination_reason",None)
    reasons=[]
    if not isinstance(text,str) or not text.strip():
        return QualityResult("INVALID",("EMPTY",))
    if "\ufffd" in text:
        reasons.append("REPLACEMENT_CHARACTER")
    if any(ord(ch)<32 and ch not in "\n\t\r" for ch in text):
        reasons.append("CONTROL_CHARACTER")
    # Obvious consecutive repetition, avoiding semantic claims about repeated words.
    if re.search(r"(.{5,}?)\1{2,}",text):
        reasons.append("REPEATED_FRAGMENT")
    if termination=="MAX_TOKENS":
        reasons.append("MAX_TOKENS")
    if reasons:
        return QualityResult("INCOMPLETE_OR_INVALID",tuple(reasons))
    return QualityResult("VALID",())
