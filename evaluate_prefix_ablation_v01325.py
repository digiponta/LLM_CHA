"""v0.13.25 prefix ablation evaluator: token-rank and continuation diagnostics.

Compare ranks across targets cautiously: the first target tokens differ.
"""
import argparse
import json
from pathlib import Path
from diagnose_teacher_forcing_v01324 import token_analysis

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--prefix",type=Path,default=Path("results/prefix_ablation_v01325"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/prefix_ablation_v01325_evaluation.json"))
    a=p.parse_args()
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from unapproved_corpus_learning_v0139 import load_jsonl
    import torch
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer=Tokenizer.load(str(a.tokenizer))
    summary={};details=[]
    for key in ("A_LABEL","B_RAW","D_NATURAL"):
        path=Path(str(a.prefix)+"_"+key+".pt")
        data=Path(str(a.prefix)+"_"+key+".jsonl")
        if not path.exists() or not data.exists():p.error(f"missing experiment: {key}")
        model,_=LanguageModel.load_checkpoint(str(path),device=device)
        model.eval()
        batch=[]
        for row in load_jsonl(data):
            stats=token_analysis(model,tokenizer,row["user"],row["assistant"],prefix_tokens=8)
            batch.append({"subject":row.get("subject"),"knowledge_id":row.get("knowledge_id"),**stats})
        if not batch:p.error(f"no rows: {key}")
        summary[key]={"cases":len(batch),
            "mean_nll":sum(x["teacher_forced_nll"] for x in batch)/len(batch),
            "mean_rank1_rate":sum(x["teacher_forced_rank1_rate"] for x in batch)/len(batch),
            "first_token_rank1":sum(x["first_target_rank"]==1 for x in batch),
            "free_first_token_match":sum(x["free_divergence"]!=0 for x in batch),
            "prefix_first_token_match":sum(x["prefix_divergence"]!=0 for x in batch)}
        details.append({"variant":key,"cases":batch})
    report={"version":"v0.13.25","base_conditions":"common source checkpoint",
            "independent_holdout":False,"summary":summary,"details":details,
            "production_unchanged":True}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print("report:",a.output)
if __name__=="__main__":main()
