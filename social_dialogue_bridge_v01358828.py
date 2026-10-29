"""Conservative context-aware social response bridge (not model training).

Handles explicit user experience statements without hallucinating facts.
All unrecognized utterances continue to the existing LLM runtime.
"""
import re

def social_reply(utterance, topic="", recent_products=()):
    s=(utterance or "").strip()
    if not s or s.startswith("/"):
        return None
    if re.search(r"[？?]|^(?:何|なぜ|どうして|どこ|いつ|誰)",s):
        return None
    if re.search(r"(?:満足した|満足です|満足だった)",s):
        return "そう、満足できたのね。気に入ったようでよかった。"
    if re.search(r"(?:美味しかった|おいしかった|良かった|よかった)",s):
        return "気に入ったんだね。ほかに印象に残ったことはある？"
    if re.search(r"(?:酸味|甘味|甘み|苦味|苦み|香り|味).*(?:良かった|よかった|強かった|弱かった|した|だった)",s):
        return "味の印象を教えてくれたんだね。ほかに気づいたことはある？"
    if re.search(r"(?:飲んだ|飲みました|食べた|食べました)$",s):
        verb="飲んだ" if "飲" in s else "食べた"
        subject=re.sub(r"(?:を)?(?:飲んだ|飲みました|食べた|食べました)$","",s).strip()
        if not subject:
            return None
        if subject=="黒耳":
            known=next((x for x in recent_products if "黒耳" in x),None)
            if known:
                return f"そう、{known}を飲んだんだね。どんな味だった？"
        if len(subject)>60:
            return None
        followup="どんな味だった？" if verb=="飲んだ" else "おいしかった？"
        return f"そう、{subject}を{verb}んだね。{followup}" if False else (
            f"そう、{subject}を飲んだんだね。{followup}" if verb=="飲んだ"
            else f"そう、{subject}を食べたんだね。{followup}")
    return None
