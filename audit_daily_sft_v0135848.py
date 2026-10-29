"""v0.13.58.48 expanded daily dialogue corpus structural audit."""
import argparse,json
from pathlib import Path
from train_daily_generation_v0135847 import dataset

def audit(path):
    train,holdout,protected=dataset(path)
    by_category={}
    for r in train:by_category[r["category"]]=by_category.get(r["category"],0)+1
    if len(train)<40 or len(holdout)<8:raise ValueError("insufficient expanded dataset")
    if min(by_category.values())<4:raise ValueError("unbalanced categories")
    seen=set()
    for r in train+holdout+protected:
        normalized="".join(r["user"].split()).rstrip("！？!?。.")
        if normalized in seen:raise ValueError("duplicate normalized question")
        seen.add(normalized)
    return {"status":"STRUCTURAL_PASS","train":len(train),"holdout":len(holdout),
            "protected":len(protected),"train_categories":by_category,
            "holdout_independent":False,
            "human_review_complete":False,"production_approved":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_expanded_v0135848.jsonl"))
    args=p.parse_args()
    print(json.dumps(audit(args.source),ensure_ascii=False,indent=2))
