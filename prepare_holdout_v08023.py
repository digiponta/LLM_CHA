"""v0.8.0.23: safely stage independently curated UNSEEN_FACT holdouts.

No scraping or fabricated answers. The input JSON must contain human-curated
source citations and reference answers. Nothing is written without --write.
"""
import argparse
import json
from pathlib import Path
from unapproved_llm_intake_v074446 import _read
from unapproved_holdout_gate_v08021 import formal_holdout_gate
from unapproved_holdout_audit_v08022 import audit
from unapproved_holdout_v08020 import validate_holdout

def prepare(source,train_store,output,min_records=5,write=False):
    source=Path(source)
    output=Path(output)
    if source.resolve()==output.resolve():
        raise ValueError("INPUT_OUTPUT_OVERLAP")
    if not source.is_file():
        return {"status":"INPUT_NOT_FOUND","path":str(source),
                "hint":"Create a human-curated holdout JSON with at least five UNSEEN_FACT records.",
                "written":False}
    dataset=json.loads(source.read_text(encoding="utf-8"))
    rows=_read(train_store)["candidates"]
    training_ids=[r.get("id") for r in rows]
    # The formal holdout measures unseen facts; question paraphrases sharing
    # trained answers belong in the separate paraphrase probe.
    kinds=[r.get("evaluation_kind") for r in dataset.get("records",[])
           if isinstance(r,dict)]
    if kinds and any(k!="UNSEEN_FACT" for k in kinds):
        return {"status":"REVIEW_REQUIRED","reasons":["FORMAL_HOLDOUT_REQUIRES_UNSEEN_FACT"],
                "written":False}
    gate=formal_holdout_gate(dataset,rows,training_ids,min_records=min_records)
    if gate["status"]!="READY":
        return {"status":"NOT_READY","reasons":gate["reasons"],
                "validated_count":gate["validated_count"],"written":False}
    # Audit exact data using a temporary copy, without touching the destination.
    import tempfile
    with tempfile.TemporaryDirectory() as folder:
        tmp=Path(folder)/"stage.json"
        tmp.write_text(json.dumps(dataset,ensure_ascii=False),encoding="utf-8")
        review=audit(tmp,train_store)
    if review["status"]!="AUDITED" or any(
            row.get("flags") for row in review.get("details",[])):
        return {"status":"REVIEW_REQUIRED","reasons":[
            flag for row in review.get("details",[]) for flag in row.get("flags",[])],
            "written":False}
    # Passing lexical checks is not evidence of independent sources.
    if not write:
        return {"status":"READY_FOR_REVIEW","record_count":len(dataset["records"]),
                "written":False,"semantic_independence_verified":False}
    if output.exists():
        return {"status":"OUTPUT_EXISTS","written":False,"path":str(output)}
    output.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive creation avoids overwriting an earlier evaluation dataset.
    with output.open("x",encoding="utf-8") as stream:
        json.dump(dataset,stream,ensure_ascii=False,indent=2)
        stream.write("\n")
    return {"status":"STAGED","record_count":len(dataset["records"]),
            "written":True,"path":str(output),
            "semantic_independence_verified":False}

def main():
    parser=argparse.ArgumentParser(description="Review and stage independently curated holdouts")
    parser.add_argument("source",help="curated input JSON with at least five unseen facts")
    parser.add_argument("--store",default="data/unapproved_llm_candidates_v074446.json")
    parser.add_argument("--output",default="data/unapproved_holdout_v08020.json")
    parser.add_argument("--write",action="store_true",help="write only if all gates pass")
    args=parser.parse_args()
    print(json.dumps(prepare(args.source,args.store,args.output,write=args.write),
                     ensure_ascii=False,indent=2))
if __name__=="__main__":main()
