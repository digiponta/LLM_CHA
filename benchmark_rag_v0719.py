"""v0.7.19 benchmark: Evidence-only vs Adapter-only vs RAG generation."""
import argparse,json
from pathlib import Path
from dual_semantic_memory_v071 import DualMemory
from experimental_backend_v0711 import ExperimentalBackend
from experimental_dual_path_v0718 import answer as dual_answer
from experimental_rag_v0719 import run_question

UNKNOWN=("v079実験で紫の窓の符号は何ですか",
         "v079実験で黄色い扉の符号は何ですか")
def evaluate(memory,holdouts,backend):
    rows=json.loads(Path(holdouts).read_text(encoding="utf-8"))
    cases=[]
    for item in rows:
        direct=dual_answer(memory,item["question"],mode="evidence")
        adapter=dual_answer(memory,item["question"],mode="adapter",backend=backend)
        rag=run_question(memory,item["question"],backend)
        ref=item["reference"]
        cases.append({"question":item["question"],"reference":ref,
          "retrieval_correct":direct.get("candidate_id")==item["candidate_id"],
          "evidence_exact":direct.get("answer")=="【未承認・候補知識】"+ref,
          "adapter_exact":adapter.get("answer")=="【未承認・実験的回答】"+ref,
          "rag_exact":rag.get("answer")=="【未承認・検索拡張回答】"+ref,
          "adapter_route":adapter["route"],"rag_route":rag["route"],
          "rag_generated":rag.get("generated"),"rag_reason":rag.get("reason")})
    unknown=[]
    for question in UNKNOWN:
        unknown.append({"question":question,
          "direct":dual_answer(memory,question,mode="evidence")["route"],
          "rag":run_question(memory,question,backend)["route"]})
    return {"version":"v0.7.19","holdout_count":len(cases),
       "retrieval_correct":sum(r["retrieval_correct"] for r in cases),
       "evidence_exact":sum(r["evidence_exact"] for r in cases),
       "adapter_exact":sum(r["adapter_exact"] for r in cases),
       "rag_exact":sum(r["rag_exact"] for r in cases),
       "unknown_count":len(unknown),
       "unknown_rejected":sum(x["direct"]=="EXPERIMENTAL_UNKNOWN" and x["rag"]=="EXPERIMENTAL_UNKNOWN" for x in unknown),
       "cases":cases,"unknown_cases":unknown,
       "factual_verification":"NOT_PERFORMED","auto_promote":False,
       "production_integrated":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--approved",default="results/multi_fact_v0715/dataset/approved.jsonl")
    p.add_argument("--candidates",default="results/multi_fact_v0715/dataset/candidates.jsonl")
    p.add_argument("--holdouts",default="results/multi_fact_v0715/dataset/holdouts.json")
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--adapter",default="results/multi_fact_v0715/experimental-adapter.pt")
    p.add_argument("--output",default="results/multi_fact_v0719/comparison.json")
    a=p.parse_args()
    memory=DualMemory(a.approved,a.candidates)
    backend=ExperimentalBackend(a.base,a.tokenizer,a.adapter)
    report=evaluate(memory,a.holdouts,backend)
    out=Path(a.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("version","holdout_count","retrieval_correct","evidence_exact","adapter_exact","rag_exact","unknown_count","unknown_rejected","production_integrated")},ensure_ascii=False,indent=2))
    print("report:",out)
if __name__=="__main__":main()
