"""Pure GUI-facing diagnostic adapter: never rewrite a chat.py answer."""
from japanese_repair_gate_v09745 import repair_and_recheck
from emotion_response_plan_v09743 import plan

def semantic_preview(utterance,answer):
    """Read-only preview; contains no side effects or persistent writes."""
    utterance=str(utterance or "").strip()
    answer=str(answer or "").strip()
    if not utterance or not answer or utterance.startswith("/"):
        return None
    p=plan(utterance)
    if p is None:
        return None
    r=repair_and_recheck(utterance,answer)
    return {
        "decision":r.decision,
        "reason":r.reason,
        "original":answer,
        "suggestion":r.selected_response if r.decision in ("REPAIRED","FALLBACK") else None,
        "primary":p.primary_emotion,
        "secondary":list(p.secondary_emotions),
        "overall_axis":p.overall_axis,
        "overall_value":p.overall_emotion_value,
        "read_only":True,
        "approved_for_training":False,
    }

def format_preview(preview):
    if preview is None:return ""
    primary=preview["primary"] or "-"
    secondary=",".join(preview["secondary"]) or "-"
    text="Semantic診断（表示専用）: {} / primary={} / secondary={}".format(
        preview["decision"],primary,secondary)
    if preview["suggestion"]:
        text+="\n修正候補（未送信）: "+preview["suggestion"]
    elif preview["decision"]=="ABSTAIN":
        text+="\n判定対象外：元のAI応答は承認されていません。"
    return text
