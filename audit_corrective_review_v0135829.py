"""Review/audit assistant-reviewed corrective SFT candidates; no training.
These eight prompts were previously used for evaluation, so they MUST NOT
serve as independent holdout after inclusion in a training dataset.
"""
import argparse,collections,hashlib,json
from pathlib import Path
from dialogue_format_v0135817 import dialogue_for

def audit(source,output):
    if output.exists():raise FileExistsError(output)
    rows=[json.loads(line) for line in source.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if not rows:raise ValueError("empty")
    if len({r.get("id") for r in rows})!=len(rows):raise ValueError("duplicate ids")
    if len({r.get("user") for r in rows})!=len(rows):raise ValueError("duplicate questions")
    required={"id","user","assistant","domain","approved","reviewer","review_type","review_date","approval_scope","training_authorized","production_promotion_allowed","source_probe"}
    for r in rows:
        if not required.issubset(r):raise ValueError("missing fields")
        if r["approved"] is not True or r["reviewer"]!="ChatGPT GPT-6" or r["review_type"]!="assistant_content_review":
            raise ValueError("not reviewed")
        if r["approval_scope"]!="candidate_corrective_sft_only" or r["training_authorized"] is not False or r["production_promotion_allowed"] is not False:
            raise ValueError("unsafe approval")
        dialogue_for(r["user"],r["assistant"])
    report={"version":"v0.13.58.29","status":"ASSISTANT_CONTENT_REVIEW_RECORDED",
        "candidate_records":len(rows),"categories":dict(collections.Counter(r["domain"] for r in rows)),
        "source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
        "approved_for_candidate_dataset":True,
        "training_authorized":False,"training_performed":False,
        "human_reviewer_attested":False,
        "independent_holdout_verified":False,"production_promotion_allowed":False,
        "evaluation_leakage_warning":"All 8 source prompts occurred in v0.13.58.27 raw-generation evaluation; do not reuse as independent test or generalization metric.",
        "required_next_step":"Prepare new unexposed paraphrase holdout before evaluating corrective learning."}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/corrective_sft_reviewed_v0135829.jsonl"))
    p.add_argument("--output",type=Path,default=Path("results/corrective_review_v0135829.json"))
    a=p.parse_args();r=audit(a.source,a.output)
    print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
