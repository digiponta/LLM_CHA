"""v0.4.28.40 — explicit human review and export, no automatic training.

Two-stage workflow: template -> human edits decisions -> validated export.
Candidate IDs, source line and answer are immutable. Review decisions are
not inferred from Quality Gate status. No synthetic negatives are gold.
"""
import argparse,hashlib,json
from pathlib import Path

SCHEMA="LLM_CHA_HUMAN_REVIEW_v042840"
CHOICES={"ACCEPT","REJECT","SKIP"}
def template(quality):
    if quality.get("version")!="v0.4.28.39":raise ValueError("requires v0.4.28.39 quality JSON")
    return {"schema":SCHEMA,"source_input_sha256":quality.get("input_sha256"),
        "instructions":"Edit decision from PENDING to ACCEPT/REJECT/SKIP; ACCEPT must have nonempty reviewer, verified_question, review_note. No automatic approval.",
        "reviews":[{"id":c["id"],"source":c["source"],"answer":c["answer"],
                    "gate_status":c["gate_status"],"suggested_question":c.get("suggested_question"),
                    "decision":"PENDING","verified_question":"","reviewer":"","review_note":""}
                   for c in quality["candidates"]]}
def apply(quality,reviews):
    if quality.get("version")!="v0.4.28.39" or reviews.get("schema")!=SCHEMA:
        raise ValueError("input version or review schema mismatch")
    if quality.get("input_sha256")!=reviews.get("source_input_sha256"):
        raise ValueError("review provenance mismatch")
    source={x["id"]:x for x in quality["candidates"]}
    rows=reviews.get("reviews")
    if not isinstance(rows,list) or len(rows)!=len(source):
        raise ValueError("review must cover all candidates")
    seen=set();approved=[];status={"ACCEPT":0,"REJECT":0,"SKIP":0,"PENDING":0}
    for row in rows:
        key=row.get("id")
        if key in seen or key not in source:raise ValueError("unknown/duplicate candidate id")
        seen.add(key);original=source[key]
        if row.get("source")!=original["source"] or row.get("answer")!=original["answer"] or row.get("gate_status")!=original["gate_status"]:
            raise ValueError("review attempted to alter immutable source")
        decision=row.get("decision")
        if decision not in status:raise ValueError("invalid decision")
        status[decision]+=1
        if decision=="ACCEPT":
            if original["gate_status"]!="HOLD":raise ValueError("only HOLD proposals may be approved")
            question=row.get("verified_question")
            reviewer=row.get("reviewer")
            note=row.get("review_note")
            if not isinstance(question,str) or not 5<=len(question.strip())<=160 or not question.strip().endswith(("?","？","。")):
                raise ValueError("approved question invalid")
            if not isinstance(reviewer,str) or not reviewer.strip() or not isinstance(note,str) or not note.strip():
                raise ValueError("reviewer and note required")
            if question.strip()==original.get("question") and not note.strip():raise ValueError("unreviewed source")
            approved.append({"id":key,"question":question.strip(),"answer":original["answer"],
                             "label":True,"label_source":"HUMAN_REVIEW",
                             "reviewer":reviewer.strip(),"review_note":note.strip(),
                             "source":original["source"],"human_verified":True,
                             "usage":"TRAIN_ELIGIBLE_CANDIDATE_ONLY"})
    return {"version":"v0.4.28.40","mode":"HUMAN_REVIEWED_POSITIVE_EXPORT",
      "source_input_sha256":quality.get("input_sha256"),
      "accepted":status["ACCEPT"],"rejected":status["REJECT"],"skipped":status["SKIP"],"pending":status["PENDING"],
      "positives":approved,"negatives":[],"hard_negatives":[],
      "train_ready":False,"evaluation_ready":False,"runtime_modified":False,
      "note":"Only positive candidate export; needs independent vetted negatives, subject-group split and licensing/privacy audit."}

def safe_write(path,obj):
    if path.exists() or path.is_symlink():raise ValueError("output exists")
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write("\n")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--quality",default="results/japanese_foundation_qa_quality_v042839.json")
    p.add_argument("--make-template",default=None)
    p.add_argument("--review",default=None)
    p.add_argument("--output",default=None)
    a=p.parse_args()
    try:
        if (a.make_template is None)==(a.review is None):
            raise ValueError("choose exactly one of --make-template or --review")
        path=Path(a.quality)
        if not path.is_file() or path.is_symlink():raise ValueError("quality file missing")
        quality=json.loads(path.read_text(encoding="utf-8-sig"))
        if a.make_template:
            if a.output:raise ValueError("--output unused in template mode")
            obj=template(quality);target=Path(a.make_template)
        else:
            if not a.output:raise ValueError("--output required for review mode")
            review_path=Path(a.review)
            if not review_path.is_file() or review_path.is_symlink():raise ValueError("review file missing")
            obj=apply(quality,json.loads(review_path.read_text(encoding="utf-8-sig")))
            target=Path(a.output)
        safe_write(target,obj)
        print(json.dumps({"mode":obj.get("mode","REVIEW_TEMPLATE"),"count":len(obj.get("reviews",obj.get("positives",[]))),"accepted":obj.get("accepted",0)},ensure_ascii=False))
    except (OSError,ValueError,TypeError,KeyError) as e:p.exit(1,f"review workflow failed: {e}\n")
if __name__=="__main__":main()
