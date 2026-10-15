"""v0.5.17.2: safe evidence-grounded conversational fallback.

A Wikipedia extract is an unverified external source, not model knowledge.
This guard avoids passing a well-grounded lookup into unrelated raw generation.
"""
import re

def grounded_reply(wiki, user_text):
    if not isinstance(wiki,dict) or wiki.get("status")!="FOUND":
        return None
    title=wiki.get("title","")
    excerpt=wiki.get("extract","")
    source=wiki.get("url","")
    if not title or not excerpt or not source.startswith("https://ja.wikipedia.org/wiki/"):
        return None
    first=re.split(r"[。\n]",excerpt.strip(),maxsplit=1)[0].strip()
    if len(first)<15 or len(first)>350:
        return None
    # Do not portray this response as neural model generation or verified truth.
    summary=first.rstrip("。")+"。"
    if len(summary)>200: summary=summary[:197]+"…"
    if any(word in user_text for word in ("記事","読んだ","見た","話")):
        ending="その記事では、どんな使い方が紹介されていましたか？"
    else:
        ending="どの部分について話しましょうか？"
    return {"answer":"Wikipediaによると、"+summary+" "+ending,
            "route":"WIKIPEDIA_GROUNDED_FALLBACK",
            "source":source,"verified":False,"train_ready":False}
