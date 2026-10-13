"""Wikipedia provenance display for reviewed/explicitly requested source answers.

This is formatting only. It does NOT learn, approve, verify or route answers.
"""
from __future__ import annotations
from urllib.parse import urlsplit

PREFIX="wiki>"
ALLOWED=("WIKIPEDIA_ARTICLE_EVIDENCE","WIKIPEDIA_SEARCH_RESULT","WIKIPEDIA_EXTRACTIVE_CANDIDATE")
def format_wiki_answer(answer, *, source, article_url, factual_truth, eligible_for_training=False, explicit_source_request=False):
    if source not in ALLOWED:
        raise ValueError("wiki prefix requires explicit Wikipedia provenance")
    if not isinstance(article_url,str):
        raise ValueError("missing Wikipedia URL")
    parsed=urlsplit(article_url)
    if not (parsed.scheme=="https" and parsed.hostname=="ja.wikipedia.org"
            and parsed.username is None and parsed.password is None
            and parsed.port in (None,443) and parsed.path.startswith("/wiki/")
            and not parsed.query and not parsed.fragment):
        raise ValueError("untrusted Wikipedia URL")
    if factual_truth!="UNVERIFIED" or eligible_for_training is not False:
        raise ValueError("unexpected Wikipedia truth/training state")
    if explicit_source_request is not True:
        raise ValueError("explicit request required for unverified Wikipedia response")
    if not isinstance(answer,str) or not answer.strip() or len(answer)>6000:
        raise ValueError("invalid answer")
    if any(c in answer for c in ("\r","\x00")):
        raise ValueError("unsafe answer control")
    text=answer.strip()
    if text.startswith(("wiki>","AI>","persona>")):
        raise ValueError("answer already prefixed")
    return "wiki> 【Wikipedia参照・未検証】\n"+text+"\n出典: "+article_url

def from_article_alignment(proposition, alignment, *, explicit_source_request=False):
    if not isinstance(alignment,dict) or alignment.get("version") not in ("v0.4.10","v0.4.12"):
        raise ValueError("unsupported alignment report")
    if alignment.get("truth_promotions")!=0 or alignment.get("semantic_memory_writes")!=0 or alignment.get("training_enabled") is not False:
        raise ValueError("unsafe alignment report")
    if not isinstance(proposition,dict) or proposition not in alignment.get("propositions",[]):
        raise ValueError("proposition not in trusted report")
    if proposition.get("review_state")!="PENDING_REVIEW":
        raise ValueError("unexpected review state")
    return format_wiki_answer(
        proposition["proposition_literal"],
        source="WIKIPEDIA_EXTRACTIVE_CANDIDATE",
        article_url=alignment["article_url"],
        factual_truth=proposition["factual_truth"],
        eligible_for_training=proposition["eligible_for_training"],
        explicit_source_request=explicit_source_request)
