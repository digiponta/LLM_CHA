"""v0.4.17 read-only diagnostic for v0.4.16 Wikipedia fallback."""
from __future__ import annotations
import hashlib
from urllib.parse import quote
from urllib.error import HTTPError,URLError
from unknown_wikipedia_fallback_v0416 import extract_topic
from wikipedia_article_evidence_v0409 import fetch_article
from article_proposition_alignment_v0412 import align
from wikipedia_answer_prefix_v04141 import from_article_alignment
from definition_property_boundary_v0414 import classify

def diagnose(question, *, focus=None, fetcher=fetch_article):
    result={"version":"v0.4.17","status":"NOT_APPLICABLE","reason":"NOT_DEFINITION_QUERY",
            "answer":None,"topic":None,"article_url":None,"article_obtained":False,
            "proposition_count":0,"boundary_classes":[],
            "factual_truth":"UNVERIFIED","eligible_for_training":False,
            "truth_promotions":0,"semantic_memory_writes":0,"training_enabled":False}
    topic=extract_topic(question)
    if not topic or (focus is not None and topic!=focus.strip()):
        return result
    result["topic"]=topic
    if any(c in topic for c in (":","/","\\","\n","\r","\t","..","%","&","#","=")):
        result.update(status="BLOCKED",reason="INVALID_TOPIC")
        return result
    candidate={"id":hashlib.sha256(topic.encode()).hexdigest()[:24],
        "content_sha256":hashlib.sha256(("auto:"+topic).encode()).hexdigest(),
        "concept":topic,"title":topic,
        "url":"https://ja.wikipedia.org/wiki/"+quote(topic.replace(" ","_"),safe="")}
    try:
        evidence=fetcher(candidate,5)
    except (HTTPError,URLError,TimeoutError,OSError) as exc:
        result.update(status="FAILED",reason="FETCH_ERROR",error_type=type(exc).__name__)
        return result
    except (ValueError,KeyError,TypeError,IndexError) as exc:
        # v0.4.9 reports API missing pages and title mismatches as ValueError;
        # do not misreport them as proven network failures or missing articles.
        result.update(status="FAILED",reason="ARTICLE_REJECTED_OR_NOT_FOUND",error_type=type(exc).__name__)
        return result
    if not isinstance(evidence,dict) or evidence.get("concept")!=topic or evidence.get("article_url")!=candidate["url"]:
        result.update(status="BLOCKED",reason="EVIDENCE_REJECTED")
        return result
    result.update(article_obtained=True,article_url=candidate["url"])
    if (evidence.get("version")!="v0.4.9" or evidence.get("factual_truth")!="UNVERIFIED"
        or evidence.get("eligible_for_training") is not False
        or evidence.get("revision_content_verified") is not False
        or evidence.get("human_article_reviewed") is not False
        or evidence.get("is_full_article") is not False):
        result.update(status="BLOCKED",reason="EVIDENCE_REJECTED")
        return result
    try:
        aligned=align(evidence)
        result["proposition_count"]=aligned["proposition_count"]
        if not aligned["propositions"]:
            result["boundary_classes"]=[x["classification"] for x in classify(evidence)["items"]]
            result.update(status="NO_ANSWER",reason="NO_DEFINITION")
            return result
        result["answer"]=from_article_alignment(aligned["propositions"][0],aligned,explicit_source_request=True)
        result.update(status="HIT",reason="EXTRACTIVE_DEFINITION")
    except (ValueError,KeyError,TypeError,IndexError) as exc:
        result.update(status="BLOCKED",reason="EVIDENCE_REJECTED",error_type=type(exc).__name__)
    return result
