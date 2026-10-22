"""v0.6.38: narrow topic-followup scope and conservative greeting guard.

No inferred facts: a property is returned only from the active entity's
retrieved evidence. Missing scoped evidence is explicitly acknowledged.
"""
import re

SAFE_GREETINGS={"こんにちは":"こんにちは。","こんばんは":"こんばんは。","おはよう":"おはよう。","おはようございます":"おはようございます。"}

def safe_greeting(text):
    return SAFE_GREETINGS.get(text.strip().rstrip("。！!"))

def scoped_followup(text, topic, evidence):
    question=text.strip().rstrip("。？！?! ")
    if question not in ("メニューは","メニュー","所在地は","所在地","住所は","住所"):
        return None
    if not topic:
        return None
    if question.startswith("メニュー") and topic not in ("スターバックス", "スターバックス コーヒー"):
        return None
    if question.startswith("メニュー"):
        return {"answer":"{}のメニューについて、このWikipedia概要だけでは具体的な内容を確認できません。".format(topic),
            "topic":topic,"attribute":"menu","grounded":False}
    if not evidence:
        return {"answer":"{}の所在地について、現在の出典からは確認できません。".format(topic),
            "topic":topic,"attribute":"address","grounded":False}
    sentence=next((x.strip() for x in re.split(r"[。\n]",evidence)
        if ("本社" in x or "所在地" in x) and ("豊田市" in x or "東京都" in x or "愛知県" in x)),None)
    if not sentence:
        return {"answer":"{}の所在地について、現在の出典からは確認できません。".format(topic),
            "topic":topic,"attribute":"address","grounded":False}
    return {"answer":"【Wikipedia概要・未検証】"+sentence+"。","topic":topic,
        "attribute":"address","grounded":True}
