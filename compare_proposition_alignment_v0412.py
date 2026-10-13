"""v0.4.12 comparative diagnostic: original 20 plus separate adversarial set."""
from __future__ import annotations
import argparse
import json
from evaluate_japanese_proposition_v0411 import CASES,synthetic_evidence
from article_proposition_alignment_v0410 import align as original
from article_proposition_alignment_v0412 import align as expanded
from external_candidate_store_v0407 import _atomic_write

# Written for this change, NOT an independent blind holdout.
ADVERSARIAL=[
("neg-composed","小説は文学の形式ではないのである。",False),
("neg-plain","小説は文学ではない。",False),
("neg-polite","小説は文学ではありません。",False),
("quoted-claim","「小説は文学である。」と書かれている。",False),
("hedged-claim","小説は文学であるらしい。",False),
("question-claim","小説は文学である？",False),
("hypothetical","小説は文学であると仮定する。",False),
("another-subject","小説家は文学者である。",False),
("toha-new","小説とは文学である。",True),
("desu-new","小説は文学です。",True),
("means-new","小説は創作文学を意味する。",True),
("reverse-new","文学の一形式が小説である。",True),
]

def measure(cases,fn):
    d=[]
    for name,text,expected in cases:
        result=fn(synthetic_evidence(text))
        yes=result["proposition_count"]>0
        for p in result["propositions"]:
            if text[p["evidence_start"]:p["evidence_end"]]!=p["evidence_text"]:
                raise ValueError("invalid evidence span")
        d.append({"id":name,"expected":expected,"extracted":yes,"match":expected==yes})
    tp=sum(x["expected"] and x["extracted"] for x in d)
    fp=sum(not x["expected"] and x["extracted"] for x in d)
    fn_=sum(x["expected"] and not x["extracted"] for x in d)
    tn=sum(not x["expected"] and not x["extracted"] for x in d)
    return {"total":len(d),"tp":tp,"fp":fp,"fn":fn_,"tn":tn,
            "precision":tp/(tp+fp) if tp+fp else None,
            "recall":tp/(tp+fn_) if tp+fn_ else None,"details":d}

def compare():
    original_set=[(n,t,y) for n,t,y,_ in CASES]
    return {"version":"v0.4.12","protocol":"RETROSPECTIVE_TUNING_DIAGNOSTIC_NOT_BLIND_HOLDOUT",
            "v0411_cases":{"baseline":measure(original_set,original),"expanded":measure(original_set,expanded)},
            "adversarial_cases":{"baseline":measure(ADVERSARIAL,original),"expanded":measure(ADVERSARIAL,expanded)},
            "truth_promotions":0,"semantic_memory_writes":0,"training_enabled":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report")
    args=p.parse_args()
    result=compare()
    if args.report:_atomic_write(args.report,result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
