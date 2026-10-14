"""v0.4.28.18: read-only character bigram overlap baseline. NOT semantic relevance."""
import argparse,csv,json,re
from pathlib import Path
from review_semantic_relevance_v042813 import FIELDS,summarize

def bigrams(s):
    s="".join(c.lower() for c in s if c.isalnum())
    return set(s[i:i+2] for i in range(len(s)-1))

def evaluate(validation,review_rows):
    report=summarize(validation,review_rows)
    labels={(x["id"],int(x["turn"])):x["labels"].get("final_relevant") for x in report["manual_evaluations"]}
    out=[]
    for row in validation["records"]:
        q,a=row["question"],row.get("final_answer")
        qg=bigrams(q); ag=bigrams(a) if isinstance(a,str) else set()
        score=round(len(qg&ag)/len(qg),6) if qg and ag else None
        out.append({"id":row["id"],"turn":row["turn"],"lexical_overlap":score,
                    "human_relevant":labels.get((row["id"],row["turn"])),
                    "semantic_relevance":"NOT_MEASURED","gate_modified":False})
    if len(out)!=64:raise ValueError("expected 64 turns")
    labeled=[x for x in out if x["human_relevant"] is not None and x["lexical_overlap"] is not None]
    return {"version":"v0.4.28.18","mode":"OFFLINE_LEXICAL_DIAGNOSTIC",
      "not_semantic_classifier":True,"total_turns":64,
      "paired_labels":len(labeled),"paired_positive":sum(x["human_relevant"] is True for x in labeled),
      "paired_negative":sum(x["human_relevant"] is False for x in labeled),"records":out}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--validation",required=True);p.add_argument("--reviews",required=True);p.add_argument("--output",required=True)
    a=p.parse_args()
    try:
        dst=Path(a.output)
        if dst.exists():raise ValueError("output exists")
        v=json.loads(Path(a.validation).read_text(encoding="utf-8"))
        with Path(a.reviews).open(encoding="utf-8-sig",newline="") as f:
            rd=csv.DictReader(f)
            if rd.fieldnames!=FIELDS:raise ValueError("invalid headers")
            rows=list(rd)
        result=evaluate(v,rows)
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2)
        print(json.dumps({k:result[k] for k in ("total_turns","paired_labels","paired_positive","paired_negative")}))
    except (OSError,ValueError) as e:p.exit(1,f"evaluation failed: {e}\n")
if __name__=="__main__":main()
