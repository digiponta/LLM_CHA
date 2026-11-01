"""Shadow-only RSE evaluation against provisional annotations.

Never emits original dialogue text or enables live candidate adoption.
"""
import argparse,json
from pathlib import Path
from prepare_rse_holdout_v013588308 import construct
from review_rse_holdout_v013588309 import validate
from rse_accept_candidate_v013588307 import assess

def ratio(a,b):
    return a/b if b else None

def evaluate(holdout,review,items,require_distinct_query=True):
    validity=validate(holdout,review)
    if validity["status"]!="LABELING_COMPLETE":
        raise ValueError("REVIEW_NOT_COMPLETE_OR_INVALID: "+str(validity["errors"]))
    if review.get("source_split")!=holdout.get("split"):
        raise ValueError("SOURCE_SPLIT_MISMATCH")
    ids={x["id"]:x for x in items}
    original={x["id"]:x for x in holdout["cases"]}
    if set(ids)!=set(original):
        raise ValueError("SOURCE_IDS_NOT_IDENTICAL_TO_HOLDOUT")
    for id_,meta in original.items():
        sample=ids[id_]
        if sample["dialogue_id"]!=meta["dialogue_id"]:
            raise ValueError("DIALOGUE_ID_MISMATCH")
        if len(sample["question"])!=meta["question_chars"] or len(sample["answer"])!=meta["answer_chars"]:
            raise ValueError("SOURCE_LENGTH_MISMATCH")
    rows=[];counts={"tp":0,"fp":0,"tn":0,"fn":0,"review_positive":0,"review_negative":0}
    for case in review["cases"]:
        source=ids[case["id"]]
        query=case["new_query"].strip()
        if require_distinct_query and query==source["question"].strip():
            raise ValueError("NON_INDEPENDENT_QUERY: "+case["id"])
        label=bool(case["intent_match"] and case["slot_match"] and case["answer_suitable"] and not case["persona_transfer_risk"])
        result=assess(query,source["question"],source["answer"])
        choice=result["status"]
        if choice not in ("REJECT","MANUAL_REVIEW_REQUIRED","ACCEPT_CANDIDATE"):
            raise ValueError("UNKNOWN_DECISION")
        group=("tp" if label else "fp") if choice=="ACCEPT_CANDIDATE" else (
            ("fn" if label else "tn") if choice=="REJECT" else
            ("review_positive" if label else "review_negative"))
        counts[group]+=1
        rows.append({"id":case["id"],"dialogue_id":case["dialogue_id"],
                     "ai_provisional_suitable":label,"decision":choice,
                     "reasons":result["reasons"],"intent":result["intent"]})
    tp,fp,tn,fn=(counts[k] for k in ("tp","fp","tn","fn"))
    accepted=tp+fp;positive=tp+fn+counts["review_positive"]
    negative=fp+tn+counts["review_negative"]
    total=len(rows)
    return {"status":"AI_PROVISIONAL_SHADOW_EVALUATION","cases":total,
            "labels_source":"AI_PROVISIONAL_NOT_HUMAN_VERIFIED",
            "dialogue_split":holdout["split"],"independent_external_holdout":False,
            "live_auto_accept_enabled":False,
            "confusion_with_abstention":counts,
            "accept_candidate_precision":ratio(tp,accepted),
            "accept_candidate_recall":ratio(tp,positive),
            "false_acceptance_rate_negative":ratio(fp,negative),
            "candidate_coverage":ratio(accepted,total),
            "abstention_rate":ratio(counts["review_positive"]+counts["review_negative"],total),
            "positive_count":positive,"negative_count":negative,
            "rows":rows}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="data-src/real-persona-chat")
    p.add_argument("--holdout",default="results/rse_independent_holdout_v013588308.json")
    p.add_argument("--review",default="results/rse_human_review_v013588309.json")
    p.add_argument("--output",default="results/rse_shadow_evaluation_v013588310.json")
    p.add_argument("--speaker",default="CP")
    a=p.parse_args()
    holdout=json.loads(Path(a.holdout).read_text(encoding="utf-8-sig"))
    review=json.loads(Path(a.review).read_text(encoding="utf-8-sig"))
    items,_=construct(a.source,a.speaker,holdout["split"],len(holdout["cases"]))
    result=evaluate(holdout,review,items)
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
