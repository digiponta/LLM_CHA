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
        self.experience_product=None
        self.taste_turns=0
        self.awaiting_conclusion=False
    def reset(self):
        self.awaiting_category=False
        self.experience_product=None
        self.taste_turns=0
        self.awaiting_conclusion=False
    def respond(self, question, text):
        q=str(question or "").strip().rstrip("。？！? ")
        if not text:
            self.reset()
            return None
        from clipboard_product_resolution_v09720 import classify
        resolved=classify(text,q)
        if resolved and resolved["status"]=="AMBIGUOUS":
            self.awaiting_category=False
            self.experience_product=None
            self.taste_turns=0
            self.awaiting_conclusion=False
            return "どちらの商品について？ " + "、".join(resolved["products"][:3])
        if resolved and resolved["status"]=="EXACT" and not (resolved["intent"]=="TASTE" and self.taste_turns and self.experience_product):
            product=resolved["product"]
            self.awaiting_category=False
            self.awaiting_conclusion=False
            self.experience_product=product
            self.taste_turns=2
            if resolved["intent"]=="EXPERIENCE":
                return "そう、{}を飲んだのね。どんな味だった？".format(product)
            if resolved["intent"]=="TASTE":
                return "そう、{}についての味の感想なのね。ほかに印象に残ったところはある？".format(product)
        experiential=product_experience(q,text)
        if experiential is not None:
            self.awaiting_category=False
            products=sum(section_items(text).values(),[])
            named=sorted((x for x in products if x in q),key=len,reverse=True)
            self.experience_product=named[0] if named else None
            self.taste_turns=2
            self.awaiting_conclusion=False
            return experiential
        # v0.9.7.29: accept an explicit evaluation at any point during
        # a current product experience, without requiring two taste turns.
        from daily_evaluation_intent_v09729 import classify_evaluation
        evaluation=classify_evaluation(question)
        if evaluation and (self.experience_product or self.awaiting_conclusion):
            self.experience_product=None
            self.taste_turns=0
            self.awaiting_conclusion=False
            self.awaiting_category=False
            return evaluation["response"]
        # A short-lived, explicit taste dialogue. Never capture unrelated queries.
        if self.taste_turns and self.experience_product:
            taste_terms=("酸味","甘さ","甘かった","酸っぱ","苦味","苦かっ",
                         "美味し","おいし","チョコレート","味","飲みやす")
            question_terms=("ですか","ますか","教えて","何","種類","一覧","検索","ググって","ぐぐって")
            if any(x in q for x in taste_terms) and not any(x in q for x in question_terms):
                self.taste_turns-=1
                if self.taste_turns==0:
                    self.experience_product=None
                    self.awaiting_conclusion=True
                if "酸味" in q and "甘さ" in q:
                    return "酸味と甘さのバランスが良かったのね。飲みやすかった？"
                if "チョコレート" in q and "甘" in q:
                    return "黒耳の部分はチョコレートで甘かったのね。印象に残ったんだ。"
                return "そう、味についての感想を聞けてよかった。ほかに印象に残ったところはある？"
            self.experience_product=None
            self.taste_turns=0
        if self.awaiting_conclusion:
            # Conclusion is accepted only immediately after taste dialogue.
            self.awaiting_conclusion=False
            if q in ("満足","満足した","とても満足した","満足だった","よかった","良かった","おいしかった","美味しかった"):
                return "そう、満足できたのね。気に入ったようでよかった。"
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
