"""Prepare known v072 paraphrase probes without touching Semantic Memory."""
import argparse,json
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from benchmark_generalization_v078 import make_holdout

def prepare(approved,candidates,output):
    memory=DualMemory(approved,candidates)
    pending=[r for r in memory.candidates() if r["status"]=="PENDING"]
    if not pending:raise ValueError("no pending candidates")
    rows=[]
    for r in pending:
        rows.append({"knowledge_id":r["id"],"split":"train",
                     "question":r["question"],"reference":r["answer"]})
        if r["question"]=="v072実験の合言葉は何ですか":
            for item in make_holdout(r):
                rows.append({"knowledge_id":r["id"],"split":"paraphrase",
                             "question":item["question"],"reference":r["answer"]})
    out=Path(output)
    if out.resolve() in (Path(approved).resolve(),Path(candidates).resolve()):
        raise ValueError("must not overwrite memory")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"train":len(pending),"paraphrase":len(rows)-len(pending),"output":str(out)}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--approved",default="data/approved_v071.jsonl")
    p.add_argument("--candidates",default="data/candidates_v071.jsonl")
    p.add_argument("--output",default="results/experimental_longitudinal_v0726/probes.json")
    a=p.parse_args()
    print(json.dumps(prepare(a.approved,a.candidates,a.output),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
