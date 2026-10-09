"""v0.2.14: paired real/shuffled/no-history teacher-forced evaluation.

Interpret context_gain_real_vs_shuffled cautiously: history length and formatting
are fixed, but the unrelated history may still have topical overlap.
"""
from __future__ import annotations
import argparse,json,random
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from diagnose_models_v0213 import score_answer,last_user_only

def swap_history(prompt,alternate):
    if "\nAI:" not in prompt:return None
    tail=last_user_only(prompt)
    historical=alternate.rsplit("\n人: ",1)[0] if "\n人: " in alternate else ""
    if not historical:return None
    return historical+"\n"+tail

def evaluate(model,tok,rows,limit,seed=42):
    rng=random.Random(seed)
    subset=rows[:limit]
    eligible=[row for row in subset if "\nAI:" in row["user"]]
    if len(eligible)<2:raise ValueError("At least two multi-turn rows required")
    indices=list(range(len(eligible)));shuffled=indices[:]
    rng.shuffle(shuffled)
    if any(x==y for x,y in zip(indices,shuffled)):
        shuffled=indices[1:]+indices[:1]
    totals={"real":0.,"none":0.,"shuffled":0.,"tokens":0,"rows":0,"skipped":0}
    for i,row in enumerate(eligible):
        alternate=eligible[shuffled[i]]["user"]
        changed=swap_history(row["user"],alternate)
        if changed is None:totals["skipped"]+=1;continue
        scores=[score_answer(model,tok,q,row["assistant"]) for q in
                (row["user"],last_user_only(row["user"]),changed)]
        if any(s is None for s in scores):totals["skipped"]+=1;continue
        for label,score in zip(("real","none","shuffled"),scores):
            totals[label]+=score[0]
        totals["tokens"]+=scores[0][1];totals["rows"]+=1
    if not totals["tokens"]:raise ValueError("No scorable examples")
    n=totals["tokens"]
    return {"rows":totals["rows"],"skipped":totals["skipped"],"answer_tokens":n,
            "nll_real":round(totals["real"]/n,5),
            "nll_no_context":round(totals["none"]/n,5),
            "nll_shuffled":round(totals["shuffled"]/n,5),
            "gain_real_over_none":round((totals["none"]-totals["real"])/n,5),
            "gain_real_over_shuffled":round((totals["shuffled"]-totals["real"])/n,5)}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dataset",default="data/dialogue_generalization_v0212/test.jsonl")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--models",nargs="+",default=["model/model-llm-cha-quality-v028.pt","model/model-llm-cha-dialogue-v0211.pt","model/model-llm-cha-generalization-v0212.pt"])
    p.add_argument("--max-rows",type=int,default=300)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--output",default="results/context_ablation_v0214.json")
    a=p.parse_args()
    rows=[json.loads(x) for x in Path(a.dataset).read_text(encoding="utf-8").splitlines() if x.strip()]
    tok=Tokenizer.load(a.tokenizer);device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    report={}
    for path in a.models:
        model,_=LanguageModel.load_checkpoint(path,device);model.eval()
        report[path]=evaluate(model,tok,rows,a.max_rows,a.seed)
        del model
        if device.type=="cuda":torch.cuda.empty_cache()
    result={"dataset":a.dataset,"seed":a.seed,"metrics":report}
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
