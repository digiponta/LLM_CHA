"""Report source aliases and review readiness; never auto-approve human review."""
import argparse,json,hashlib
from pathlib import Path
from evidence_alias_normalization_v013588261 import diagnose
from evaluate_real_evidence_v013588260 import validate_review

def inspect(dataset):
    rows=[]
    for item in dataset.get("cases",[]):
        ev=item["evidence"];src=item["source"]
        digest=hashlib.sha256(ev.get("excerpt","").encode("utf-8")).hexdigest()
        alias=diagnose(item["question"],ev)
        rows.append({"id":item["id"],"question":item["question"],
                     "source_title":src.get("title"),"url":ev.get("url"),
                     "source_hash_matches":digest==src.get("excerpt_sha256"),
                     "truncated":src.get("truncated"),
                     "review_status":item.get("review",{}).get("status"),
                     "alias":alias})
    return {"status":"REAL_EVIDENCE_DIAGNOSTIC_ONLY",
            "cases":len(rows),"review_gate":validate_review(dataset),
            "records":rows,"holdout_approved":False,
            "production_changed":False,
            "note":"Alias mapping is diagnostic; real evidence is not an independent holdout and is not auto-approved."}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",default="data/wiki_evidence_review_v013588260.json")
    p.add_argument("--output",default="results/evidence_alias_review_v013588261.json")
    a=p.parse_args()
    result=inspect(json.loads(Path(a.data).read_text(encoding="utf-8-sig")))
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"cases":result["cases"],
        "review_gate":result["review_gate"],"report":str(path)},ensure_ascii=False))
if __name__=="__main__":main()
