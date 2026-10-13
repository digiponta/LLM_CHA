"""LLM_CHA v0.4.11: frozen, offline Japanese proposition generalization evaluation.

Reports baseline extraction precision/recall on hand-authored diagnostic examples.
Does not change extractor, Truth Gate, Semantic Memory, or learning.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from article_proposition_alignment_v0410 import align
from external_candidate_store_v0407 import _atomic_write

CASES=[
("simple-dearu","小説は文学の形式である。",True,"in_pattern"),
("simple-da","小説は文学だ。",True,"in_pattern"),
("metadata","小説（しょうせつ、英: novel（長編））は文学の形式である。",True,"in_pattern"),
("spaced","小説は、文学の形式である。",True,"in_pattern"),
("second-sentence","これは概説である。小説は文学の形式である。",True,"in_pattern"),
("toha","小説とは文学の一形式である。",True,"generalization"),
("one-of","小説は文学の形式の一つ。",True,"generalization"),
("means","小説は文学的な創作を指す。",True,"generalization"),
("copula-desu","小説は文学の形式です。",True,"generalization"),
("passive-concept","文学の形式の一つが小説である。",True,"generalization"),
("non-definition","小説には多くの種類がある。",False,"negative"),
("other-subject","小説家は作品を書く人である。",False,"negative"),
("secondary-mention","推理小説は小説の一種である。",False,"negative"),
("negation","小説は文学の形式ではない。",False,"negative"),
("false-denial","小説は文学ではないのである。",False,"negative"),
("quoted","「小説は文学の形式である。」という引用がある。",False,"negative"),
("question","小説は文学の形式であるか？",False,"negative"),
("hedged","小説は文学の形式であるらしい。",False,"negative"),
("unrelated","今日は晴れである。",False,"negative"),
("hypothetical","もし小説は文学であると仮定する。",False,"negative"),
]

def synthetic_evidence(lead):
    return {"version":"v0.4.9","candidate_id":"diagnostic-only",
            "candidate_content_sha256":"0"*64,"concept":"小説",
            "article_title":"小説","article_url":"https://ja.wikipedia.org/wiki/小説",
            "extract_sha256":hashlib.sha256(lead.encode()).hexdigest(),
            "lead_extract":lead,"pageid":4295,"revid":0,
            "factual_truth":"UNVERIFIED","eligible_for_training":False,
            "revision_content_verified":False}

def evaluate(cases=CASES):
    names=[name for name,*_ in cases]
    if len(names)!=len(set(names)):raise ValueError("duplicate case identifiers")
    details=[]
    for name,sentence,expected,family in cases:
        result=align(synthetic_evidence(sentence))
        predicted=result["proposition_count"]>0
        spans_ok=all(sentence[p["evidence_start"]:p["evidence_end"]]==p["evidence_text"]
                     for p in result["propositions"])
        if not spans_ok:raise ValueError("invalid source alignment in "+name)
        details.append({"id":name,"family":family,"expected_extract":expected,
                        "predicted_extract":predicted,"match":expected==predicted,
                        "extracted_count":result["proposition_count"]})
    tp=sum(x["expected_extract"] and x["predicted_extract"] for x in details)
    fp=sum(not x["expected_extract"] and x["predicted_extract"] for x in details)
    fn=sum(x["expected_extract"] and not x["predicted_extract"] for x in details)
    tn=sum(not x["expected_extract"] and not x["predicted_extract"] for x in details)
    precision=tp/(tp+fp) if tp+fp else None
    recall=tp/(tp+fn) if tp+fn else None
    return {"version":"v0.4.11","protocol":"HAND_AUTHORED_DIAGNOSTIC_NOT_INDEPENDENT_HOLDOUT",
            "baseline":"v0.4.10_UNMODIFIED","total":len(details),
            "tp":tp,"fp":fp,"fn":fn,"tn":tn,
            "precision":precision,"recall":recall,
            "balanced_accuracy":((tp/(tp+fn))+(tn/(tn+fp)))/2 if (tp+fn) and (tn+fp) else None,
            "details":details,"truth_promotions":0,"semantic_memory_writes":0,
            "training_enabled":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",default=None)
    args=p.parse_args()
    result=evaluate()
    if args.report:_atomic_write(args.report,result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
