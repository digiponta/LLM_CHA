"""v0.5.64: bounded Wikipedia follow-up after the current article is exhausted.

Every answer is an exact span from a linked article explicitly mentioning the
original topic. Relatedness alone never establishes a factual relationship.
"""
import re
from urllib.parse import quote
from wikipedia_acquisition_v0517 import _request
from wiki_persona_multiturn_v0520 import FOLLOWUPS
from scientific_evidence_v0563 import scientific_sentences, scientific_prose, display_latex

class EvidenceContinuation:
    def __init__(self):
        self.identity = None
        self.seen = set()

    def reset(self):
        self.identity = None
        self.seen.clear()

    def next(self, wiki, question, persona="nagato", fetch=None, max_articles=6):
        if not isinstance(wiki, dict) or wiki.get("status") != "FOUND":
            self.reset()
            return {"status": "NO_CONTEXT"}
        if not isinstance(question, str) or question.strip().rstrip("。！？!? ") not in FOLLOWUPS:
            return {"status": "NOT_APPLICABLE"}
        title = wiki.get("title")
        url = wiki.get("url")
        if not isinstance(title, str) or not title or not isinstance(url, str) or not url.startswith("https://ja.wikipedia.org/wiki/"):
            return {"status": "INVALID_SOURCE"}
        if not isinstance(max_articles, int) or not 1 <= max_articles <= 8:
            return {"status": "INVALID_LIMIT"}
        identity = (title, url)
        if identity != self.identity:
            self.identity = identity
            self.seen.clear()
        try:
            data = _request({"action":"query","prop":"links","titles":title,
                             "pllimit":40,"format":"json","formatversion":2}, fetch)
            pages = data.get("query", {}).get("pages", [])
            if not pages or pages[0].get("missing") or pages[0].get("title") != title:
                return {"status":"SOURCE_MISMATCH"}
            links = [item.get("title") for item in pages[0].get("links", [])
                     if isinstance(item, dict) and isinstance(item.get("title"), str)
                     and ":" not in item["title"] and item["title"] != title]
            visited = []
            for linked_title in sorted(set(links))[:max_articles]:
                detail = _request({"action":"query","prop":"extracts","titles":linked_title,
                                   "explaintext":1,"exchars":5000,
                                   "format":"json","formatversion":2}, fetch)
                rows = detail.get("query", {}).get("pages", [])
                if not rows or rows[0].get("missing") or rows[0].get("title") != linked_title:
                    continue
                extract = rows[0].get("extract", "")
                if not isinstance(extract, str):
                    continue
                visited.append(linked_title)
                for sentence in scientific_sentences(extract):
                    if not 20 <= len(sentence) <= 1000 or title not in sentence:
                        continue
                    if not scientific_prose(sentence):
                        continue
                    key = (linked_title, sentence)
                    if key in self.seen:
                        continue
                    self.seen.add(key)
                    display = display_latex(sentence)
                    answer = ("関連するWikipedia記事「"+linked_title+"」には、"+display+"。とある。"
                              if persona == "nagato" else
                              "関連するWikipedia記事「"+linked_title+"」には、"+display+"。と記載されています。")
                    return {"status":"FOUND","answer":answer,"title":linked_title,
                            "source":"https://ja.wikipedia.org/wiki/"+quote(linked_title.replace(" ","_")),
                            "route":"PERSONA_WIKIPEDIA_EVIDENCE_CONTINUATION",
                            "quality_gate":"LINKED_ARTICLE_EXPLICIT_TOPIC_EXACT_SPAN",
                            "truth_state":"EXTERNAL_UNVERIFIED","verified":False,
                            "train_ready":False,"auto_promote":False,
                            "visited":visited}
            return {"status":"EVIDENCE_EXHAUSTED","visited":visited,
                    "verified":False,"train_ready":False}
        except (OSError, ValueError, TypeError, KeyError, TimeoutError) as exc:
            return {"status":"LOOKUP_FAILED","reason":type(exc).__name__}
