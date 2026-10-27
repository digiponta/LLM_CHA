"""v0.13.29 evaluate first-token learning curve and stability replay NLL."""
import argparse
import json
from pathlib import Path
from compare_first_token_learning_v01328 import measure
from train_b_raw_epoch_sweep_v01329 import EPOCHS,plan

def summarize(rows):
    n=len(rows)
    return {"cases":n,
      "first_rank1":sum(r["first_rank"]==1 for r in rows),
      "mean_first_nll":sum(r["first_nll"] for r in rows)/n,
      "mean_answer_nll":sum(r["answer_nll"] for r in rows)/n,
      "mean_first_rank":sum(r["first_rank"] for r in rows)/n}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--prefix",type=Path,default=Path("results/b_raw_epoch_v01329"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--data",type=Path,default=Path("results/unapproved_b_raw_v01326.jsonl"))
    p.add_argument("--stability",type=Path,default=Path("data/stability_replay_v104.jsonl"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/b_raw_epoch_curve_v01329.json"))
    a=p.parse_args()
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from unapproved_corpus_learning_v0139 import load_jsonl
    if not a.data.exists():p.error("missing training data")
    rows=load_jsonl(a.data)
    stability=load_jsonl(a.stability) if a.stability.exists() else []
    tokenizer=Tokenizer.load(str(a.tokenizer))
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checks=[{"epochs":0,"checkpoint":str(a.base)}]+plan(a.prefix)
    details={};summary={}
    for job in checks:
        path=Path(job["checkpoint"])
        if not path.exists():p.error(f"missing checkpoint {path}")
        model,_=LanguageModel.load_checkpoint(str(path),device=device)
        model.eval()
        data=[measure(model,tokenizer,r["user"],r["assistant"]) for r in rows]
        st=[measure(model,tokenizer,r["user"],r["assistant"]) for r in stability if r.get("user") and r.get("assistant")]
        key="E"+str(job["epochs"])
        summary[key]={**summarize(data),
                      "stability_cases":len(st),
                      "stability_mean_answer_nll":sum(r["answer_nll"] for r in st)/len(st) if st else None}
        details[key]=data
    report={"version":"v0.13.29","independent_holdout":False,"summary":summary,"details":details,
            "production_unchanged":True}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print("report:",a.output)
if __name__=="__main__":main()
