"""v0.4.16 automatic, read-only Wikipedia fallback for UNKNOWN concept definitions.

Exact-title Japanese Wikipedia lookup only. Does not train or mutate memory.
"""
from __future__ import annotations
import hashlib
import re
from urllib.parse import quote
from wikipedia_article_evidence_v0409 import fetch_article
from article_proposition_alignment_v0412 import align
from wikipedia_answer_prefix_v04141 import from_article_alignment

def extract_topic(question):
    if not isinstance(question,str) or len(question)>120:return None
    s=question.strip()
    m=re.fullmatch(r"([^\s、。！？?!/\\]{1,50}?)(?:とは|って何|とは何|について教えて)[？?。!！]*",s)
    return m.group(1).strip() if m else None

def automatic_wikipedia_answer(question, *, focus=None, fetcher=fetch_article):
    """Returns display text or None, with no memory writes or learning."""
    topic=extract_topic(question)
    if not topic:return None
    if focus is not None and focus.strip() and topic!=focus.strip():
        return None
    if any(x in topic for x in (":","/","\\","\n","\r","\t","..","%","&","#","=")):
        return None
    candidate={"id":hashlib.sha256(topic.encode()).hexdigest()[:24],
               "content_sha256":hashlib.sha256(("auto:"+topic).encode()).hexdigest(),
               "concept":topic,"title":topic,
               "url":"https://ja.wikipedia.org/wiki/"+quote(topic.replace(" ","_"),safe="")}
    # fetch_article validates non-redirect, exact-title MediaWiki article and source.
    evidence=fetcher(candidate,timeout=5)
    if not isinstance(evidence,dict) or evidence.get("concept")!=topic or evidence.get("article_url")!=candidate["url"]:
        raise ValueError("retrieved article provenance mismatch")
    if (evidence.get("version")!="v0.4.9"
        or evidence.get("factual_truth")!="UNVERIFIED"
        or evidence.get("eligible_for_training") is not False
        or evidence.get("revision_content_verified") is not False
        or evidence.get("human_article_reviewed") is not False
        or evidence.get("is_full_article") is not False):
        raise ValueError("unsafe article evidence")
    alignment=align(evidence)
    if not alignment["propositions"]:return None
    return from_article_alignment(alignment["propositions"][0],alignment,
                                  explicit_source_request=True)
