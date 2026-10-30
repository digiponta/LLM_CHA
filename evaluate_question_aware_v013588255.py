"""Run question-aware evidence extraction against saved snapshot without generating."""
import argparse,json
from pathlib import Path
from question_aware_evidence_v013588255 import answer_or_abstain
DEFAULT_QUESTIONS=["宇宙とは","ビッグバンはいつ起きたのか","宇宙はなぜ膨張するのか","宇宙の化学組成は"]
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--evidence-json",default="results/evidence_snapshot_v013588249.json")
 p.add_argument("--question",action="append")
 p.add_argument("--output",default="results/question_aware_evidence_v013588255.json")
 a=p.parse_args()
 evidence=json.loads(Path(a.evidence_json).read_text(encoding="utf-8-sig"))
 cases=[answer_or_abstain(q,evidence) for q in (a.question or DEFAULT_QUESTIONS)]
 report={"status":"QUESTION_AWARE_EVIDENCE_DIAGNOSTIC","cases":cases,"extract_count":sum(c["status"]=="EXTRACT_ACCEPTED" for c in cases),"abstain_count":sum(c["status"]!="EXTRACT_ACCEPTED" for c in cases),"production_changed":False,"evidence_file":a.evidence_json}
 output=Path(a.output);output.parent.mkdir(parents=True,exist_ok=True)
 output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"status":report["status"],"extract_count":report["extract_count"],"abstain_count":report["abstain_count"],"report":str(output)},ensure_ascii=False))
if __name__=="__main__":main()
