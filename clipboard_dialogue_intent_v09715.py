"""Conservative intent routing for temporary clipboard menu conversations.

No model learning or persistent personalization. Treat first-person product
experience as dialogue, not a request for a product listing.
"""
import re
from clipboard_grounded_qa_v0977 import section_items

EXPERIENCE = re.compile(r"(飲んだことがある|飲んだことある|食べたことがある|食べたことある|試したことがある|買ったことがある|飲んでみた|食べてみた|美味しかった|おいしかった|好きだった|苦手だった)")
MENU = re.compile(r"(メニュー|ドリンク|飲み物|ビバレッジ|フード|フラペチーノ|ラテ)")
def product_experience(question, text):
    if not EXPERIENCE.search(question) or re.search(r"(ですか|ますか|ある[？?]|どんな|何が)",question):
        return None
    sections=section_items(text)
    products=sum(sections.values(),[])
    named=sorted((x for x in products if x in question),key=len,reverse=True)
    if not named:
        return None
    return "そう、{}を試したことがあるのね。どんな味だった？".format(named[0])
class ClipboardDialogue:
    def __init__(self):
        self.awaiting_category=False
    def reset(self):
        self.awaiting_category=False
    def respond(self, question, text):
        q=str(question or "").strip().rstrip("。？！? ")
        if not text:
            self.reset()
            return None
        experiential=product_experience(q,text)
        if experiential is not None:
            self.awaiting_category=False
            return experiential
        categories={"ドリンク":"ドリンクの種類は","飲み物":"ドリンクの種類は",
                    "ビバレッジ":"ドリンクの種類は","フード":"フードには何がある？",
                    "食べ物":"フードには何がある？","フラペチーノ":"フラペチーノの種類は"}
        if self.awaiting_category and q in categories:
            from clipboard_grounded_qa_v0977 import answer_from_clipboard
            result=answer_from_clipboard(text,categories[q])
            self.awaiting_category=False
            return result["answer"] if result else None
        self.awaiting_category=False
        if ("メニュー" in q and not EXPERIENCE.search(q)
                and ("スターバックス" in q or q in ("メニューは","メニュー"))):
            sections=section_items(text)
            available=[label for label,items in sections.items() if items]
            if available:
                self.awaiting_category=True
                names="ドリンク、フード" if len(available)>1 else ("ドリンク" if "ビバレッジ" in available else "フード")
                return "コピーしたページには{}のメニューがあります。どちらを知りたい？（未検証）".format(names)
        return None
