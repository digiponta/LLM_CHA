"""LLM_CHA v0.4.10 — strictly extractive article-to-proposition alignment.

Only a narrow 'XはYである/だ' pattern is supported. No paraphrase,
semantic inference, factual verification or knowledge promotion.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
from external_candidate_store_v0407 import _atomic_write

MAX_FILE=128_000
PATTERN=re.compile(r"(?P<subject>[^。！？\n]{1,80}?)は[、\s]*(?P<predicate>[^。！？\n]{2,200}?(?:である|だ))(?=。|$)")

def align(evidence):
    if not isinstance(evidence,dict) or evidence.get("version")!="v0.4.9":
        raise ValueError("invalid article evidence version")
    for k in ("candidate_id","candidate_content_sha256","extract_sha256","lead_extract","article_url","concept","article_title"):
        if not isinstance(evidence.get(k),str) or not evidence[k]:
            raise ValueError("missing evidence field: "+k)
    lead=evidence["lead_extract"]
    if (len(lead)>6000 or hashlib.sha256(lead.encode("utf-8")).hexdigest()!=evidence["extract_sha256"]
        or evidence.get("factual_truth")!="UNVERIFIED"
        or evidence.get("eligible_for_training") is not False
        or evidence.get("revision_content_verified") is not False):
        raise ValueError("evidence integrity or safety mismatch")
    topic=evidence["concept"].strip()
    # Avoid a substring match, e.g., '小説家' must not stand in for '小説'.
    # Parenthetical pronunciations immediately after the topic are permitted.
    head=re.compile(r"^"+re.escape(topic)+r"(?:（[^）\n]{1,100}）)?は[、\s]*")
    matches=[]
    for sentence_match in re.finditer(r"[^。！？\n]+(?:[。！？]|$)",lead):
        sentence=sentence_match.group()
        m=head.match(sentence.strip())
        if not m:continue
        predicate=sentence.strip()[m.end():].rstrip("。！？").strip()
        if not (predicate.endswith("である") or predicate.endswith("だ")):continue
        if not 2<=len(predicate)<=200:continue
        # Exact source span, not a regenerated assertion.
        start=sentence_match.start()+len(sentence)-len(sentence.lstrip())
        end=start+len(sentence.strip())
        original=lead[start:end]
        if original!=sentence.strip():raise ValueError("span integrity failure")
        matches.append({"subject":topic,"predicate":predicate,
                        "proposition_literal":original,
                        "evidence_start":start,"evidence_end":end,
                        "evidence_text":original,
                        "alignment":"EXACT_SUBJECT_AND_LITERAL_SPAN",
                        "factual_truth":"UNVERIFIED",
                        "review_state":"PENDING_REVIEW",
                        "eligible_for_training":False})
    return {"version":"v0.4.10","candidate_id":evidence["candidate_id"],
            "candidate_content_sha256":evidence["candidate_content_sha256"],
            "concept":topic,"article_url":evidence["article_url"],
            "article_title":evidence["article_title"],
            "pageid":evidence.get("pageid"),"revid":evidence.get("revid"),
            "extract_sha256":evidence["extract_sha256"],
            "revision_content_verified":False,
            "alignment_type":"RULE_BASED_EXTRACTIVE_ONLY",
            "proposition_count":len(matches),"propositions":matches,
            "truth_promotions":0,"semantic_memory_writes":0,
            "training_enabled":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--evidence",required=True)
    p.add_argument("--report",help="Optional separate diagnostic JSON path")
    a=p.parse_args()
    try:
        src=Path(a.evidence)
        if src.stat().st_size>MAX_FILE:raise ValueError("evidence file too large")
        data=json.loads(src.read_text(encoding="utf-8"))
        result=align(data)
        if a.report:
            if Path(a.report).resolve()==src.resolve():raise ValueError("refusing to overwrite evidence")
            _atomic_write(a.report,result)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError,TypeError,KeyError,json.JSONDecodeError) as e:
        p.exit(1,f"Proposition alignment failed: {type(e).__name__}: {e}\n")
if __name__=="__main__":main()
