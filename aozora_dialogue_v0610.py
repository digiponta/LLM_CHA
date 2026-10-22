"""v0.6.10: opt-in conversational literature and cat clarification state."""
import re
from aozora_literature_router_v069 import route_literature

class AozoraDialogue:
    def __init__(self, catalog):
        self.catalog=catalog
        self.active_work=None
        self.pending_cat=False

    def respond(self, message):
        text=message.strip()
        if not text or text.startswith("/"):
            return None
        if self.pending_cat:
            self.pending_cat=False
            if re.fullmatch(r"(一般的(?:な質問|な話|な猫の話)?|一般(?:的な質問)?|動物(?:の話)?|普通の猫|動物として|生き物として)[。！!？?\\s]*",text):
                self.active_work=None
                return ("一般的な猫の話ですね。猫の生態、特徴、飼育のどれについて知りたいですか？",
                        {"route":"CAT_GENERAL_CLARIFICATION","train_ready":False})
            if re.fullmatch(r"(作品|小説|吾輩|吾輩は猫である|文学|本の方)[。！!？?\s]*",text):
                self.active_work="789" if "789" in self.catalog else None
                if self.active_work:
                    return route_literature("吾輩",self.catalog)
        if re.fullmatch(r"(猫|ネコ|ねこ)(?:は|って|とは|について)?[？?]?",text):
            self.pending_cat=True
            return ("猫についての一般的な質問ですか。それとも夏目漱石の『吾輩は猫である』についてですか？",
                    {"route":"CAT_TOPIC_CLARIFY","train_ready":False})
        result=route_literature(text,self.catalog)
        if result is not None:
            meta=result[1]
            if meta.get("work_id"):self.active_work=meta["work_id"]
            return result
        if self.active_work=="789" and re.fullmatch(r"(猫の名前は|猫の名前|主人公の名前は|主人公の名前)[？?]?",text):
            return ("『吾輩は猫である』の主人公の猫には名前がありません。冒頭でも名前がまだないと語られます。",
                    {"route":"AOZORA_CONTEXT_FOLLOWUP","work_id":"789",
                     "truth_state":"SOURCE_BASED_SUMMARY","train_ready":False,"promoted":False})
        if text in ("長門","こんばんは","宇宙"):
            self.active_work=None
        return None
