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

def resolve_entity(term, lookup_fn=lookup, request_fn=_request):
    # A known, explicit article title must be fetched directly: search-result
    # ambiguity does not imply that the Wikipedia page itself is ambiguous.
    alias=ENTITY_TITLES.get(term)
    if alias:
        try:
            data=request_fn({"action":"query","prop":"extracts|info",
                "inprop":"url","titles":alias,"redirects":1,
                "explaintext":1,"exintro":1,"exchars":900,
                "format":"json","formatversion":2})
            pages=data.get("query",{}).get("pages",[])
            if pages and not pages[0].get("missing") and pages[0].get("extract","").strip():
                page=pages[0]
                title=page.get("title",alias)
                return {"status":"FOUND","term":term,"title":title,
                    "extract":page["extract"],"url":"https://ja.wikipedia.org/wiki/"+
                    quote(title.replace(" ","_")),"truth_state":"EXTERNAL_UNVERIFIED"}
        except (OSError,ValueError,KeyError,TimeoutError,TypeError):
            pass
    candidate=lookup_fn(term)
    return candidate

def article_evidence(term, attribute, lookup_fn=lookup, request_fn=_request):
    wiki=resolve_entity(term, lookup_fn, request_fn)
    if wiki.get("status") != "FOUND":
        return {"status":wiki.get("status","NOT_FOUND"),"candidates":wiki.get("candidates",[]),"reason":"ENTITY_RESOLUTION"}
    title=wiki["title"]
    try:
        data=request_fn({"action":"query","prop":"extracts","titles":title,
              "redirects":1,"explaintext":1,"exintro":0,"exchars":10000,
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
    if not hits and attribute == "歴史":
        # MediaWiki parse sections are useful when TextExtracts returns only the intro.
        try:
            sections_data=request_fn({"action":"parse","page":title,"prop":"sections","format":"json"})
            sections=sections_data.get("parse",{}).get("sections",[])
            relevant=[section for section in sections
                      if any(word in re.sub(r"<[^>]+>","",section.get("line",""))
                             for word in ("歴史","沿革"))]
            for section in relevant[:3]:
                section_data=request_fn({"action":"parse","page":title,
                    "prop":"wikitext","section":section["index"],"format":"json"})
                raw=section_data.get("parse",{}).get("wikitext",{})
                raw=raw.get("*","") if isinstance(raw,dict) else str(raw)
                # Reject all wiki/XML markup before treating a passage as prose.
                # Do not return citation fragments or partial reference tags.
                def readable_line(line):
                    line=line.strip()
                    if not (18 <= len(line) <= 300):
                        return False
                    if re.search(r"<|>|\\{\\{|\\}\\}|\\[\\[|\\]\\]|\\[https?://|\\|",line):
                        return False
                    if line.startswith(("=", "*", "#", ";", ":", "!", "{", "}")):
                        return False
                    if any(mark in line for mark in ("ref>", "citation", "脚注")):
                        return False
                    return True
                candidates=[line.strip() for line in raw.splitlines()
                            if readable_line(line)]
                if candidates:
                    hits=candidates[:1]
                    break
        except (OSError,ValueError,KeyError,TimeoutError,TypeError):
            pass
    if not hits:
        return {"status":"INSUFFICIENT","title":title,"source":wiki["url"],"reason":"NO_ATTRIBUTE_SENTENCE","extract_chars":len(full)}
    answer="【Wikipediaの関連記述・未検証】"+hits[0]
    return {"status":"FOUND","title":title,"source":wiki["url"],"answer":answer,
            "truth_state":"EXTERNAL_UNVERIFIED","train_ready":False,"auto_promote":False}
