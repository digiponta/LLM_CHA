"""Offline side-by-side question-aware and relation-bound extraction."""
import argparse,json
from pathlib import Path
from question_aware_evidence_v013588255 import answer_or_abstain as old
from evidence_relation_binding_v013588256 import answer_or_abstain as new

QUESTIONS=["宇宙とは","ビッグバンはいつ起きたのか","宇宙はなぜ膨張するのか","宇宙の化学組成は"]
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--evidence-json",default="results/evidence_snapshot_v013588249.json")
 p.add_argument("--question",action="append")
 p.add_argument("--output",default="results/evidence_relation_binding_v013588256.json")
 args=p.parse_args()
 ev=json.loads(Path(args.evidence_json).read_text(encoding="utf-8-sig"))
 records=[]
 for question in args.question or QUESTIONS:
  before=old(question,ev)
  after=new(question,ev)
  records.append({"question":question,
                  "previous_status":before["status"],"previous_sentence":before.get("sentence"),
                  "binding_status":after["status"],"subject":after.get("subject"),
                  "relation":after.get("relation"),"value":after.get("value"),
                  "selected_sentence":after.get("sentence"),"answer":after["answer"]})
 report={"status":"RELATION_BINDING_OFFLINE_DIAGNOSTIC","cases":records,
         "accepted":sum(x["binding_status"]=="BOUND_EXTRACT_ACCEPTED" for x in records),
         "abstained":sum(x["binding_status"]!="BOUND_EXTRACT_ACCEPTED" for x in records),
         "production_changed":False}
 path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":report["status"],"accepted":report["accepted"],
                   "abstained":report["abstained"],"report":str(path)},ensure_ascii=False))
if __name__=="__main__":main()
