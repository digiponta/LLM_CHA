"""v0.7.9 multi-fact adapter training and held-out paraphrase comparison."""
import argparse
import json
from pathlib import Path
from prepare_multi_knowledge_v079 import prepare
from train_experimental_adapter_v073 import run as train
from benchmark_generalization_v078 import run as benchmark

CONDITIONS=((16,30,1e-3),(32,30,1e-3))

def execute(output_dir,base,tokenizer,protected_qa=None):
    output=Path(output_dir).resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("use a new empty experiment directory")
    output.mkdir(parents=True,exist_ok=True)
    fixture=prepare(output/"dataset")
    # Approved store is deliberately empty. Independently reviewed QA can be
    # supplied to the benchmark separately, without granting those facts approval.
    checkpoints=[]
    training=[]
    for rank,epochs,lr in CONDITIONS:
        checkpoint=output/f"r{rank}_e{epochs}"/"experimental-adapter.pt"
        result=train(base,tokenizer,fixture["approved"],fixture["candidates"],
                     checkpoint,rank=rank,epochs=epochs,lr=lr)
        checkpoints.append(str(checkpoint))
        training.append({"rank":rank,"epochs":epochs,"first_loss":result["first_loss"],
                         "last_loss":result["last_loss"]})
    # Evaluation uses synthetic candidate paraphrases disjoint from training
    # question strings. Candidate answers necessarily appeared in training.
    report=benchmark(base,tokenizer,fixture["approved"],fixture["candidates"],
       checkpoints,output/"paraphrase_raw.json",fixture["holdouts"])
    scored=[]
    for condition,item in zip(training,report["results"]):
        cases=item["holdout"]["cases"]
        per_fact={}
        for case in cases:
            marker=next(row["candidate_id"] for row in
               json.loads(Path(fixture["holdouts"]).read_text(encoding="utf-8"))
               if row["question"]==case["question"])
            per_fact.setdefault(marker,[]).append(case["exact_match"]["experimental"])
        scored.append({**condition,"checkpoint":item["checkpoint"],
           "holdout_exact_base":item["holdout"]["exact_match"]["base"],
           "holdout_exact_experimental":item["holdout"]["exact_match"]["experimental"],
           "per_fact_exact":{key:sum(vals)/len(vals) for key,vals in per_fact.items()},
           "retention_status":"NOT_EVALUATED_NO_VERIFIED_PROBES",
           "deployment_approved":False})
    result={"version":"v0.7.9","candidate_count":fixture["candidate_count"],
       "paraphrase_holdouts":fixture["holdout_count"],"conditions":scored,
       "verified_protected_probes":0,"quality_pass":None,
       "note":"Synthetic fact paraphrase test only; do not interpret as independent factual generalization."}
    (output/"summary_v079.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="results/multi_knowledge_v079")
    ap.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    ap.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    a=ap.parse_args()
    print(json.dumps(execute(a.output_dir,a.base,a.tokenizer),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
