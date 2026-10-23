"""v0.7.15 isolated four-fact training and end-to-end route audit.

Does not modify production Approved Memory, Candidate Memory or checkpoints.
Protected route precedence is evaluated with a temporary approved fixture and
is not a factual retention benchmark.
"""
import argparse
import json
from pathlib import Path
from prepare_multi_knowledge_v079 import prepare,FACTS
from train_experimental_adapter_v073 import run as train_adapter
from benchmark_generalization_v078 import run as evaluate_holdout
from dual_semantic_memory_v071 import DualMemory
from experimental_backend_v0711 import ExperimentalBackend
from multi_candidate_audit_v0714 import evaluate_probes

UNKNOWN_PROBES=("v079実験で紫の窓の符号は何ですか",
                "v079実験で黄色い扉の符号は何ですか")
PROTECTED_QUESTION="v0715保護経路の確認質問"
PROTECTED_ANSWER="これは経路保護用の合成回答です。"

def summarize(audit,holdout):
    candidate_count=audit["candidate_count"]
    unknown_count=audit["unknown_count"]
    protected_count=audit["protected_count"]
    return {"candidate_count":candidate_count,
            "candidate_exact":audit["candidate_exact"],
            "candidate_exact_rate":audit["candidate_exact_rate"],
            "unknown_count":unknown_count,
            "unknown_rejected":audit["unknown_rejected"],
            "unknown_reject_rate":audit["unknown_rejected"]/unknown_count if unknown_count else None,
            "protected_count":protected_count,
            "protected_route_preserved":audit["trusted_protected_preserved"] if protected_count else None,
            "holdout_count":holdout["holdout_count"],
            "holdout_base_exact":holdout["results"][0]["holdout"]["exact_match"]["base"],
            "holdout_experimental_exact":holdout["results"][0]["holdout"]["exact_match"]["experimental"],
            "factual_verification":"NOT_PERFORMED",
            "approved_retention_certified":False,
            "auto_promote":False}

def execute(output_dir,base,tokenizer,*,rank=16,epochs=30,lr=1e-3):
    output=Path(output_dir).resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("use a new empty output directory")
    output.mkdir(parents=True,exist_ok=True)
    fixture=prepare(output/"dataset")
    memory=DualMemory(fixture["approved"],fixture["candidates"])
    # The protected fixture checks trusted routing only and is NOT externally verified.
    memory.propose(PROTECTED_QUESTION,PROTECTED_ANSWER,"synthetic:v0715:routing-only")
    protected_id=next(r["id"] for r in memory.candidates() if r["question"]==PROTECTED_QUESTION)
    memory.approve(protected_id)
    checkpoint=output/"experimental-adapter.pt"
    training=train_adapter(base,tokenizer,fixture["approved"],fixture["candidates"],
                           checkpoint,rank=rank,epochs=epochs,lr=lr)
    holdout=evaluate_holdout(base,tokenizer,fixture["approved"],fixture["candidates"],
                           [checkpoint],output/"paraphrases.json",fixture["holdouts"])
    backend=ExperimentalBackend(base,tokenizer,checkpoint)
    audit=evaluate_probes(memory,backend,unknown_questions=UNKNOWN_PROBES)
    # Only the four PENDING synthetic facts are trained; the protected synthetic
    # fixture stays in the approved store and must never enter training.
    summary=summarize(audit,holdout)
    report={"version":"v0.7.15","fixture":"synthetic-four-facts",
            "conditions":{"rank":rank,"epochs":epochs,"lr":lr},
            "training":{"first_loss":training["first_loss"],"last_loss":training["last_loss"]},
            "checkpoint":str(checkpoint),"summary":summary,
            "audit":audit,
            "holdout_cases":holdout["results"][0]["holdout"]["cases"]}
    (output/"summary_v0715.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"version":report["version"],"checkpoint":str(checkpoint),
            "training":report["training"],"summary":summary,
            "report":str(output/"summary_v0715.json")}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",default="results/multi_fact_v0715")
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--rank",type=int,default=16)
    p.add_argument("--epochs",type=int,default=30)
    p.add_argument("--lr",type=float,default=1e-3)
    a=p.parse_args()
    print(json.dumps(execute(a.output_dir,a.base,a.tokenizer,rank=a.rank,epochs=a.epochs,lr=a.lr),
                     ensure_ascii=False,indent=2))
if __name__=="__main__":main()
