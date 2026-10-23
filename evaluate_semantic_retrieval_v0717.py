"""Evaluate v0.7.17 Candidate retrieval without altering the 8 holdout questions."""
import argparse,json
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from experimental_semantic_retrieval_v0717 import route

UNKNOWN=("v079実験で紫の窓の符号は何ですか",
         "v079実験で黄色い扉の符号は何ですか")
def evaluate(approved,candidates,holdouts):
    memory=DualMemory(approved,candidates)
    rows=json.loads(Path(holdouts).read_text(encoding="utf-8"))
    cases=[]
    for item in rows:
        result=route(memory,item["question"])
        cases.append({"question":item["question"],"reference":item["reference"],
                      "route":result["route"],
                      "correct_candidate":result.get("candidate_id")==item.get("candidate_id"),
                      "reason":result["reason"]})
    rejected=[route(memory,q) for q in UNKNOWN]
    correct=sum(c["correct_candidate"] for c in cases)
    return {"version":"v0.7.17","holdout_count":len(cases),
            "retrieval_correct":correct,"retrieval_accuracy":correct/len(cases) if cases else None,
            "unknown_count":len(UNKNOWN),
            "unknown_rejected":sum(r["route"]=="EXPERIMENTAL_UNKNOWN" for r in rejected),
            "cases":cases,"auto_promote":False,
            "note":"Held-out wording evaluation only; retrieval answer is unapproved and not externally validated."}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--approved",default="results/multi_fact_v0715/dataset/approved.jsonl")
    p.add_argument("--candidates",default="results/multi_fact_v0715/dataset/candidates.jsonl")
    p.add_argument("--holdouts",default="results/multi_fact_v0715/dataset/holdouts.json")
    p.add_argument("--output",default="results/multi_fact_v0717/retrieval.json")
    a=p.parse_args()
    r=evaluate(a.approved,a.candidates,a.holdouts)
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"version":r["version"],"holdout_count":r["holdout_count"],
                      "retrieval_correct":r["retrieval_correct"],
                      "unknown_rejected":r["unknown_rejected"],
                      "output":str(dest)},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
