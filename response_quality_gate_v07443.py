"""v0.7.44.3 conservative Japanese response gate; no side effects.

A gate decision is NOT an alternative source of factual truth. Never promote
unverified evidence or treat a persona gap as authority to rewrite evidence.
"""
import re
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class Decision:
    action: str
    reasons: tuple[str, ...]
    persona_gap: bool
    def to_dict(self):
        d = asdict(self)
        d["reasons"] = list(self.reasons)
        return d

def assess_response(response: str, *, persona_gap=False, route="GENERATED", truth_state="UNKNOWN") -> Decision:
    """ACCEPT, RETRY, or HOLD. Integration must enforce decision, not only log it."""
    # A validated trusted retrieval is not subject to heuristic rewriting.
    if route in ("TRUSTED_RETRIEVAL", "APPROVED_RETRIEVAL"):
        return Decision("ACCEPT", (), bool(persona_gap))
    text = (response or "").strip()
    reasons = []
    if not text:
        reasons.append("EMPTY")
    elif len(text) > 1200:
        reasons.append("OVERSIZED")
    if "\ufffd" in text or any(ord(c) < 32 and c not in "\n\t" for c in text):
        reasons.append("INVALID_CHARACTER")
    # Exact copy loops, not legitimate repeated technical terms.
    if re.search(r"(.{5,60}?)\1{2,}", text, flags=re.DOTALL):
        reasons.append("REPETITION")
    if text.count("。") > 0 and text.count("。") >= 5:
        sentences = [s.strip() for s in text.split("。") if s.strip()]
        if len(sentences) >= 5 and max(sentences.count(s) for s in sentences) >= 3:
            reasons.append("DUPLICATE_SENTENCES")
    # Explicit evidence truth boundary; not a grammar heuristic.
    if truth_state in ("UNVERIFIED", "CONTESTED", "FALSE") and route == "GENERATED_EVIDENCE":
        reasons.append("UNVERIFIED_GENERATED_EVIDENCE")
    if reasons:
        return Decision("HOLD" if "UNVERIFIED_GENERATED_EVIDENCE" in reasons else "RETRY", tuple(reasons), bool(persona_gap))
    # persona_gap requires a second quality check by the caller; never force fallback
    # solely because persona context is missing.
    return Decision("REVIEW" if persona_gap else "ACCEPT", (), bool(persona_gap))
