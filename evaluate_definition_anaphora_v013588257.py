"""Compare v0.56 and v0.57 using the same saved Evidence."""
import argparse,json
from pathlib import Path
from evidence_relation_binding_v013588256 import answer_or_abstain as before
from evidence_definition_anaphora_v013588257 import answer_or_abstain as after
QUESTIONS=["宇宙とは","ビッグバンはいつ起きたのか","宇宙はなぜ膨張するのか","宇宙の化学組成は"]
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--evidence-json",default="results/evidence_snapshot_v013588249.json")
 p.add_argument("--output",default="results/definition_anaphora_v013588257.json")
 a=p.parse_args()
 evidence=json.loads(Path(a.evidence_json).read_text(encoding="utf-8-sig"))
 cases=[]
 for q in QUESTIONS:
  old=before(q,evidence)
  new=after(q,evidence)
  cases.append({"question":q,"previous_status":old["status"],"previous_sentence":old.get("sentence"),
                "status":new["status"],"value":new.get("value"),
                "selected_sentence":new.get("sentence"),"answer":new["answer"]})
 report={"status":"DEFINITION_ANAPHORA_OFFLINE_DIAGNOSTIC","cases":cases,
         "accepted":sum(c["status"]=="BOUND_EXTRACT_ACCEPTED" for c in cases),
         "abstained":sum(c["status"]!="BOUND_EXTRACT_ACCEPTED" for c in cases),
         "production_changed":False}
 path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":report["status"],"accepted":report["accepted"],"abstained":report["abstained"],"report":str(path)},ensure_ascii=False))
if __name__=="__main__":main()
