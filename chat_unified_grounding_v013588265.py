"""Opt-in-safe automatic routing for explicit, local Wikipedia snapshot questions.

No mutation, no network, no auto-approval; abstentions remain visible rather than
silently taking the older ungrounded route for the same recognized question.
"""
import re
from chat_grounded_bridge_v013588264 import answer as grounded_answer,DEFAULT_SNAPSHOT

QUESTION=re.compile(r"(とは(?:何|どういう意味)?|とは[？?]?|化学組成|成分(?:は|を|について)|いつ(?:起き|発生)|なぜ|どうして)")
def classify_auto(question):
    q=str(question or "").strip()
    if not q or q.startswith("/") or len(q)>160:return False
    if not QUESTION.search(q):return False
    # Only affirmative knowledge requests; protect casual/social/teaching turns.
    if re.search(r"(好き|嫌い|きれい|ありがとう|覚えて|教えます|訂正|前に話した)",q):return False
    return True

def route(question,snapshot_path=DEFAULT_SNAPSHOT):
    if not classify_auto(question):return None
    result=grounded_answer(question,snapshot_path)
    # Do not intercept unrelated topics or missing/corrupted file. Preserve
    # original chat and its existing unknown/evidence gates in those cases.
    if result["status"] in {"ABSTAIN_NO_UNIQUE_SOURCE","ABSTAIN_NO_SNAPSHOT","ABSTAIN_SNAPSHOT_ERROR"}:
        return None
    return {"route":"AUTO_GROUNDED_SNAPSHOT",**result}
