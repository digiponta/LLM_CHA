"""v0.7.44.10: narrow conversational intent adapter for cat synonyms.

This opt-in rule layer is not learned personality or general Japanese NLU.
No factual assertion, semantic promotion, or learning occurs.
"""
import re

def chat_reply(text, lexicon):
    q=(text or "").strip()
    if not q or q.startswith("/") or len(q)>70:
        return None
    match=re.fullmatch(r"(猫|ネコ|ぬこ)(?:は)?(?:好き[？?]?|好きなの[？?]?)",q)
    if match:
        return {"answer":"猫の話ならできる。どんなところが好き？",
                "intent":"PREFERENCE_QUESTION","train_ready":False}
    match=re.fullmatch(r"(猫|ネコ|ぬこ)[、,，]?かわいい(?:ね|な|よね)?[。！!]*",q)
    if match:
        return {"answer":"そう。かわいいと思う。","intent":"EMPATHY","train_ready":False}
    return None
