"""v0.2.19 conservative conversational rescue; never promotes knowledge."""
import re
from conversation_diagnostics_v026 import classify_quality

KNOWLEDGE = re.compile(r"(とは|って何|何ですか|誰ですか|について教えて|説明して|教えてください|なぜ|理由|正しい|本当|事実|真偽|定義|比較|違い)")
FOLLOWUP = re.compile(r"^(?:その話|さっきの話|それ|続きを|続けて|その続き)")
def is_casual(text, intent="general"):
    if intent not in ("general","casual","feeling","acknowledgement"):return False
    if KNOWLEDGE.search(text):return False
    if FOLLOWUP.search(text.strip()):return False
    return True

def rescue_casual_gate(*,user_text,answer,intent,semantic_ok,slot_coverage,
                       confidence,min_token_conf,mean_margin,semantic_agreement,
                       rejection_reason,internalized=False,truth_restricted=False,
                       repeat=False,context_ok=True):
    """Allow only valid small-talk questions; failures remain failures by default."""
    if internalized or truth_restricted or repeat or not context_ok:return False
    if not is_casual(user_text,intent) or not semantic_ok or slot_coverage<1:return False
    if confidence<0.45 or min_token_conf<0.05 or mean_margin<0.05:return False
    if semantic_agreement<0.90:return False
    if not re.search(r"(lexical agreement|semantic-only rescue)",rejection_reason,re.I):return False
    if not answer.strip() or len(answer.strip())<8:return False
    q=classify_quality(user_text,answer)
    if q["flag"] or q["generic"]:return False
    if any(s in answer for s in ("未学習です","わかりません","不明です")):return False
    return True

def topic_followup(current, context):
    """Preserve user-origin context for short deictic followups."""
    if not FOLLOWUP.search(current.strip()):return current
    previous=list(context.messages)[:-1]
    for entry in reversed(previous):
        text=entry["text"].strip()
        if text and len(text)<=120 and not KNOWLEDGE.search(text) and not FOLLOWUP.search(text):
            return text+"。"+current
    return current
