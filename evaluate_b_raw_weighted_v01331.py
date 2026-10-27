"""v0.13.31 compare weighted B_RAW checkpoints without promotion."""
import argparse
import json
from pathlib import Path
from compare_first_token_learning_v01328 import measure
from train_b_raw_weighted_v01331 import plan

def aggregate(rows):
    n=len(rows)
    return {"cases":n,"first_rank1":sum(x["first_rank"]==1 for x in rows),
            "mean_first_nll":sum(x["first_nll"] for x in rows)/n if n else None,
            "mean_answer_nll":sum(x["answer_nll"] for x in rows)/n if n else None}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--prefix",type=Path,default=Path("results/b_raw_weighted_v01331"))
    p.add_argument("--data",type=Path,default=Path("results/unapproved_b_raw_v01326.jsonl"))
    p.add_argument("--stability",type=Path,default=Path("data/stability_replay_v104.jsonl"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/b_raw_weighted_evaluation_v01331.json"))
    a=p.parse_args()
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from unapproved_corpus_learning_v0139 import load_jsonl
    samples=load_jsonl(a.data)
    replay=[x for x in load_jsonl(a.stability) if x.get("user") and x.get("assistant")] if a.stability.exists() else []
    if not samples:p.error("empty data")
    tokenizer=Tokenizer.load(str(a.tokenizer))
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    summary={}
    for job in plan(a.prefix):
        path=Path(job["checkpoint"])
        if not path.exists():p.error(f"missing checkpoint {path}")
        model,_=LanguageModel.load_checkpoint(str(path),device=device)
        model.eval()
        train_metrics=aggregate([measure(model,tokenizer,r["user"],r["assistant"]) for r in samples])
        stability_metrics=aggregate([measure(model,tokenizer,r["user"],r["assistant"]) for r in replay])
        summary[job["variant"]]={"training":train_metrics,"stability":stability_metrics}
    report={"version":"v0.13.31","independent_holdout":False,
            "summary":summary,"production_unchanged":True}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print("report:",a.output)
if __name__=="__main__":main()
