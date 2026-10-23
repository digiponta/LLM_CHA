"""v0.7.44.4 opt-in bounded response controller, side-effect-free.

This is an isolated orchestration primitive, NOT connected to chat.py.
"""
from dataclasses import dataclass
from response_quality_gate_v07443 import assess_response

@dataclass(frozen=True)
class ResponseResult:
    text: str
    status: str
    attempts: int
    reasons: tuple[str, ...]

def controlled_response(generate, *, persona_gap=False, route="GENERATED",
                        truth_state="UNKNOWN", retry_limit=1,
                        fallback="回答をうまく生成できませんでした。もう一度質問してください。"):
    if not isinstance(retry_limit, int) or not 0 <= retry_limit <= 2:
        raise ValueError("retry_limit must be between 0 and 2")
    reasons = []
    for attempt in range(1, retry_limit + 2):
        candidate = generate(attempt)
        decision = assess_response(candidate, persona_gap=persona_gap,
                                   route=route, truth_state=truth_state)
        reasons.extend(decision.reasons)
        if decision.action == "ACCEPT":
            return ResponseResult(candidate, "ACCEPT", attempt, tuple(reasons))
        # REVIEW needs an external reviewer. Never silently accept it.
        if decision.action == "HOLD":
            return ResponseResult(fallback, "HELD", attempt, tuple(reasons))
        if decision.action == "REVIEW":
            return ResponseResult(fallback, "REVIEW_REQUIRED", attempt, tuple(reasons))
    return ResponseResult(fallback, "FALLBACK", retry_limit + 1, tuple(reasons))
