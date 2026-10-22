"""v0.6.21 Wikipedia entity resolution and article-body attribute evidence.

Read-only; do not promote external evidence into semantic memory.
"""
import re
from urllib.parse import quote
from wikipedia_acquisition_v0517 import lookup, _request

ATTRIBUTE_WORDS = {
    "歴史": ("歴史", "沿革", "設立", "創業", "創立"),
    "所在地": ("本社", "所在地", "本店", "愛知県", "住所"),
    "特徴": ("特徴", "特色"),
    "製品": ("製品", "商品"),
    "概要": (),
    "メニュー": ("メニュー", "ドリンク", "フード"),
    "価格": ("価格", "料金"),
    "営業時間": ("営業時間", "営業"),
}
# A documented title alias, not a free-form ambiguous-result guess.
ENTITY_TITLES = {"トヨタ": "トヨタ自動車"}

def resolve_entity(term, lookup_fn=lookup):
    candidate=lookup_fn(term)
    if candidate.get("status") == "FOUND":
        return candidate
    alias=ENTITY_TITLES.get(term)
    if alias and candidate.get("status") in ("AMBIGUOUS", "NOT_FOUND", "NO_EXTRACT"):
        alternative=lookup_fn(alias)
        if alternative.get("status")=="FOUND" and alternative.get("title")==alias:
            return alternative
    return candidate

def article_evidence(term, attribute, lookup_fn=lookup, request_fn=_request):
    wiki=resolve_entity(term, lookup_fn)
    if wiki.get("status") != "FOUND":
        return {"status":wiki.get("status","NOT_FOUND"),"candidates":wiki.get("candidates",[])}
    title=wiki["title"]
    try:
        data=request_fn({"action":"query","prop":"extracts","titles":title,
              "redirects":1,"explaintext":1,"exintro":0,"exchars":12000,
              "format":"json","formatversion":2})
        pages=data.get("query",{}).get("pages",[])
        full=pages[0].get("extract","") if pages else ""
    except (OSError,ValueError,KeyError,TimeoutError,TypeError):
        full=""
    if not full:
        full=wiki.get("extract","")
    words=ATTRIBUTE_WORDS.get(attribute,(attribute,))
    # Distinguish Wikipedia body evidence from a summary of a topic.
    segments=[p.strip() for p in re.split(r"(?<=[。！？])|\n+",full) if p.strip()]
    hits=[p for p in segments if 12 <= len(p) <= 350 and
          (not words or any(w in p for w in words))]
    if not hits:
        return {"status":"INSUFFICIENT","title":title,"source":wiki["url"]}
    answer="【Wikipediaの関連記述・未検証】"+hits[0]
    return {"status":"FOUND","title":title,"source":wiki["url"],"answer":answer,
            "truth_state":"EXTERNAL_UNVERIFIED","train_ready":False,"auto_promote":False}
