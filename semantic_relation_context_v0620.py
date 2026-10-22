"""v0.6.20: generic subject + attribute resolution; no fabricated facts."""
import re

ATTRIBUTES = ("歴史", "特徴", "所在地", "メニュー", "価格", "営業時間", "概要", "製品")
_PAT = re.compile(r"^(.{2,50}?)の("+"|".join(ATTRIBUTES)+r")(?:は|について|を教えて)?[？?。\s]*$")

class RelationContext:
    def __init__(self):
        self.topic=None
    def observe(self, text):
        text=text.strip()
        if text in ("長門","こんにちは","こんばんは","おはよう","/reset"):
            self.topic=None
            return None
        m=_PAT.fullmatch(text)
        if m:
            subject,attribute=m.groups()
            self.topic=subject
            return {"subject":subject,"attribute":attribute,"kind":"explicit"}
        if self.topic and text in ATTRIBUTES:
            return {"subject":self.topic,"attribute":text,"kind":"followup"}
        if text.endswith("の話題") and len(text)>4:
            self.topic=text[:-3]
        elif text and not text.startswith("/") and not text.endswith("の話題"):
            if text not in (self.topic,):
                self.topic=None
        return None

def grounded_attribute_answer(relation, wiki):
    """Use only sentences explicitly containing the queried attribute."""
    if not isinstance(wiki,dict) or wiki.get("status")!="FOUND":return None
    source=wiki.get("url")
    if not source:return None
    body=" ".join(str(wiki.get(k,"")) for k in ("summary","extract","text","description"))
    sentences=re.split(r"(?<=[。！？])",body)
    matches=[s.strip() for s in sentences if relation["attribute"] in s and 10<=len(s.strip())<=240]
    if not matches:return None
    return {"answer":"【Wikipediaの関連記述・未検証】"+matches[0],"source":source}

def clarification(relation):
    return "{}の{}について、確認できる根拠が見つかりませんでした。内容をもう少し具体的に教えて。".format(relation["subject"],relation["attribute"])
