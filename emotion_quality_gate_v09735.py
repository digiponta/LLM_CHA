"""Fail-closed strategy-aware gate for experimental emotion generation.

Only approved, strategy-compatible full replies are eligible for approval.
This conservative gate is a diagnostic baseline, not semantic verification.
"""
from emotion_aware_dialogue_v09733 import STRATEGIES

def assess(response, decision):
    text=str(response or "").strip()
    if not decision or not decision.confident:
        return False,"no-confident-emotion"
    if not text:return False,"empty"
    if "�" in text:return False,"replacement-character"
    if len(text)>100:return False,"excessive-length"
    if text in ("樹","楽しい順","へつるは、") or "花音、花音" in text:
        return False,"known-bad-regression"
    # Until validated by a separate evaluator, allow only approved strategy
    # examples, not vaguely Japanese-looking arbitrary model completions.
    allowed={decision.response}
    if decision.primary=="ENJOYMENT":
        allowed.update(("それは良かったね。","楽しい一日だったんだね。"))
    if decision.primary=="DISAPPOINTMENT":
        allowed.add("期待外れだったんだね。")
    if decision.primary=="GREETING":
        allowed.add("こんにちは。今日はどうしましたか。")
    if decision.primary=="NON_SADNESS":
        allowed.add("悲しくなかったんだね。")
    if text not in allowed:
        return False,"unverified-response-strategy"
    return True,"approved-strategy-response"
