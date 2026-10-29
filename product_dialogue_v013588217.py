"""Session-only product dialogue grounded in currently loaded menu evidence."""
import re
from menu_evidence_v013588215 import extract_menu

class ProductDialogue:
    def __init__(self):
        self.last_product = ""
    def respond(self, utterance, records, topic):
        text = (utterance or "").strip().rstrip("。")
        if not topic or not text or re.search(r"[？?]", text):
            return None
        _, sections = extract_menu(records, topic)
        products = sections["ドリンク"] + sections["フード"]
        if not products:
            return None
        preferred = re.fullmatch(r"(.+?)(?:も)?(?:が)?好き(?:です|だ)?", text)
        consumed = re.fullmatch(r"(.+?)を?(飲んだ|飲みました|食べた|食べました)", text)
        if preferred:
            raw = preferred.group(1).strip()
            intent = "like"
        elif consumed:
            raw = consumed.group(1).strip()
            intent = "drink" if "飲" in consumed.group(2) else "eat"
        else:
            if self.last_product and re.fullmatch(r".{1,35}(?:の味がいい|がおいしい|が美味しい|が好き)", text):
                return "その味が気に入っているんだね。"
            return None
        raw = re.sub(r"(?:も|が)$", "", raw).strip()
        matches = [p for p in products if p == raw or raw in p]
        if not matches:
            return None
        # Exact match wins; partial aliases must be unique.
        product = raw if raw in matches else matches[0] if len(matches) == 1 else ""
        if not product:
            return None
        self.last_product = product
        if intent == "like":
            return f"{product}も好きなんだね。どんなところが気に入っているの？"
        if intent == "drink":
            return f"そう、{product}を飲んだんだね。どんな味だった？"
        return f"そう、{product}を食べたんだね。おいしかった？"
