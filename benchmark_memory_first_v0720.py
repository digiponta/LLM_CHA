"""v0.7.20 eight-holdout Memory-First evaluation, no training or promotion."""
import argparse,json
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from experimental_backend_v0711 import ExperimentalBackend
from experimental_memory_first_v0720 import memory_first

UNKNOWN=("v079実験で紫の窓の符号は何ですか","v079実験で黄色い扉の符号は何ですか")

def evaluate(memory,holdouts,generator=None,*,mode="evidence"):
    rows=json.loads(Path(holdouts).read_text(encoding="utf-8"))
    cases=[]
    for row in rows:
        r=memory_first(row["question"],memory,trusted_ask=lambda q:{"status":"UNKNOWN"},
                       experimental_generate=generator,enabled=True,mode=mode)
        cases.append({"question":row["question"],"expected_candidate":row["candidate_id"],
            "selected_candidate":r.get("candidate_id"),"retrieval_correct":r.get("candidate_id")==row["candidate_id"],
            "answer_exact":r.get("answer")=="【未承認・候補知識】"+row["reference"],
            "generation_consistent":r.get("generation_consistent"),"route":r["route"]})
    unknown_results=[memory_first(q,memory,trusted_ask=lambda _:{"status":"UNKNOWN"},
                       experimental_generate=generator,enabled=True,mode=mode) for q in UNKNOWN]
    return {"version":"v0.7.20","mode":mode,"count":len(cases),
        "retrieval_correct":sum(c["retrieval_correct"] for c in cases),
        "evidence_exact":sum(c["answer_exact"] for c in cases),
        "generator_consistent":sum(c["generation_consistent"] is True for c in cases),
        "unknown_count":len(unknown_results),
        "unknown_rejected":sum(r["route"]=="EXPERIMENTAL_UNKNOWN" for r in unknown_results),
        "cases":cases,"auto_promote":False,"factual_verification":"NOT_PERFORMED",
        "trusted_retention_evaluated":False,"production_integrated":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--approved",default="results/multi_fact_v0715/dataset/approved.jsonl")
    p.add_argument("--candidates",default="results/multi_fact_v0715/dataset/candidates.jsonl")
    p.add_argument("--holdouts",default="results/multi_fact_v0715/dataset/holdouts.json")
    p.add_argument("--mode",choices=("evidence","constrained"),default="constrained")
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--adapter",default="results/multi_fact_v0715/experimental-adapter.pt")
    p.add_argument("--output",default="results/multi_fact_v0720/comparison.json")
    a=p.parse_args()
    memory=DualMemory(a.approved,a.candidates)
    generator=(ExperimentalBackend(a.base,a.tokenizer,a.adapter) if a.mode=="constrained" else None)
    report=evaluate(memory,a.holdouts,generator,mode=a.mode)
    out=Path(a.output)
    inputs={Path(v).resolve() for v in (a.approved,a.candidates,a.holdouts,a.base,a.tokenizer,a.adapter)}
    if out.resolve() in inputs:raise ValueError("output path overlaps experiment input")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("version","mode","count","retrieval_correct",
        "evidence_exact","generator_consistent","unknown_count","unknown_rejected",
        "production_integrated")},ensure_ascii=False,indent=2))
    print("report:",out)
if __name__=="__main__":main()
