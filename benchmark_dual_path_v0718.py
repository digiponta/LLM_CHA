"""v0.7.18 side-by-side Candidate evidence vs Experimental Adapter benchmark."""
import argparse,json
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from experimental_backend_v0711 import ExperimentalBackend
from experimental_dual_path_v0718 import answer

def evaluate(memory,holdouts,backend):
    rows=json.loads(Path(holdouts).read_text(encoding="utf-8"))
    cases=[]
    for row in rows:
        result=answer(memory,row["question"],mode="compare",backend=backend)
        if result["route"]=="EXPERIMENTAL_UNKNOWN":
            cases.append({"question":row["question"],"retrieved":False,
                          "evidence_exact":False,"adapter_exact":False})
            continue
        expected=row["reference"]
        evidence=result["evidence"]
        adapter=result["adapter"]
        cases.append({"question":row["question"],"retrieved":True,
                      "candidate_id":evidence["candidate_id"],
                      "correct_candidate":evidence["candidate_id"]==row["candidate_id"],
                      "evidence_exact":evidence["answer"]=="【未承認・候補知識】"+expected,
                      "adapter_exact":adapter.get("answer")=="【未承認・実験的回答】"+expected,
                      "adapter_route":adapter["route"],"adapter_reason":adapter["reason"]})
    n=len(cases)
    return {"version":"v0.7.18","count":n,
            "retrieval_correct":sum(c.get("correct_candidate",False) for c in cases),
            "evidence_exact":sum(c["evidence_exact"] for c in cases),
            "adapter_exact":sum(c["adapter_exact"] for c in cases),
            "cases":cases,"truth_state":"EXPERIMENTAL_UNVERIFIED",
            "auto_promote":False,"factual_verification":"NOT_PERFORMED"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--approved",default="results/multi_fact_v0715/dataset/approved.jsonl")
    p.add_argument("--candidates",default="results/multi_fact_v0715/dataset/candidates.jsonl")
    p.add_argument("--holdouts",default="results/multi_fact_v0715/dataset/holdouts.json")
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--adapter",default="results/multi_fact_v0715/experimental-adapter.pt")
    p.add_argument("--output",default="results/multi_fact_v0718/comparison.json")
    a=p.parse_args()
    mem=DualMemory(a.approved,a.candidates)
    backend=ExperimentalBackend(a.base,a.tokenizer,a.adapter)
    result=evaluate(mem,a.holdouts,backend)
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"count":result["count"],"retrieval_correct":result["retrieval_correct"],
        "evidence_exact":result["evidence_exact"],"adapter_exact":result["adapter_exact"],
        "report":str(dest)},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
