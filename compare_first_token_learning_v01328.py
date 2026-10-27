"""v0.13.28: before/after first-token learning diagnostics for B_RAW.

Read-only; both models evaluated against identical raw answer targets.
"""
import argparse
import json
import math
from pathlib import Path
import torch
import torch.nn.functional as F

def measure(model,tokenizer,question,answer,top_k=10):
    from online_train import USER_PREFIX,AI_PREFIX
    prompt=tokenizer.encode(f"{USER_PREFIX}{question}\n{AI_PREFIX}",add_bos=True)
    target=tokenizer.encode(answer,add_eos=True)
    device=next(model.parameters()).device
    max_context=model.context_length
    # first-token inference uses the identical prompt for both checkpoints
    with torch.no_grad():
        logits=model(torch.tensor([prompt[-max_context:]],device=device))[0,-1]
        lp=F.log_softmax(logits,dim=-1)
        first=target[0]
        values,indices=lp.topk(min(top_k,len(lp)))
        first_rank=int((lp>lp[first]).sum().item()+1)
        first_prob=float(lp[first].exp().item())
        first_nll=float(-lp[first].item())
        # Per-answer teacher forcing, using the exact training prompt/target boundary.
        keep_prompt=max(1,max_context+1-len(target))
        context_prompt=prompt[-keep_prompt:]
        allowed=max(1,max_context+1-len(context_prompt))
        labels=target[:allowed]
        ids=(context_prompt+labels)[:-1]
        full=model(torch.tensor([ids],device=device))[0]
        start=len(context_prompt)-1
        log_probs=F.log_softmax(full[start:start+len(labels)],dim=-1)
        expected=torch.tensor(labels,device=device)
        nll=-log_probs.gather(1,expected[:,None]).mean().item()
    return {"first_token_id":first,"first_token_text":tokenizer.decode([first]),
            "first_rank":first_rank,"first_probability":first_prob,
            "first_nll":first_nll,"answer_nll":float(nll),
            "top_k":[{"id":int(i),"text":tokenizer.decode([int(i)]),
                      "probability":float(v.exp().item())} for v,i in zip(values,indices)]}

def compare(before,after):
    if before["first_token_id"]!=after["first_token_id"]:
        raise ValueError("different target tokens")
    return {"rank_improvement":before["first_rank"]-after["first_rank"],
            "probability_ratio":after["first_probability"]/max(before["first_probability"],1e-30),
            "first_nll_improvement":before["first_nll"]-after["first_nll"],
            "answer_nll_improvement":before["answer_nll"]-after["answer_nll"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--candidate",type=Path,default=Path("results/prefix_ablation_v01325_B_RAW.pt"))
    p.add_argument("--data",type=Path,default=Path("results/prefix_ablation_v01325_B_RAW.jsonl"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/first_token_learning_v01328.json"))
    p.add_argument("--limit",type=int,default=16)
    p.add_argument("--top-k",type=int,default=10)
    a=p.parse_args()
    if a.limit<1 or a.top_k<1:p.error("limit and top-k must be positive")
    for path in (a.base,a.candidate,a.data,a.tokenizer):
        if not path.exists():p.error(f"missing: {path}")
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from unapproved_corpus_learning_v0139 import load_jsonl
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base,_=LanguageModel.load_checkpoint(str(a.base),device=device)
    candidate,_=LanguageModel.load_checkpoint(str(a.candidate),device=device)
    base.eval();candidate.eval()
    tokenizer=Tokenizer.load(str(a.tokenizer))
    details=[]
    for row in load_jsonl(a.data)[:a.limit]:
        before=measure(base,tokenizer,row["user"],row["assistant"],a.top_k)
        after=measure(candidate,tokenizer,row["user"],row["assistant"],a.top_k)
        details.append({"subject":row.get("subject"),"knowledge_id":row.get("knowledge_id"),
                        "before":before,"after":after,"change":compare(before,after)})
    if not details:p.error("no rows")
    n=len(details)
    summary={"cases":n,
             "rank_improved":sum(x["change"]["rank_improvement"]>0 for x in details),
             "rank_unchanged":sum(x["change"]["rank_improvement"]==0 for x in details),
             "first_rank1_before":sum(x["before"]["first_rank"]==1 for x in details),
             "first_rank1_after":sum(x["after"]["first_rank"]==1 for x in details),
             "mean_first_nll_before":sum(x["before"]["first_nll"] for x in details)/n,
             "mean_first_nll_after":sum(x["after"]["first_nll"] for x in details)/n,
             "mean_answer_nll_before":sum(x["before"]["answer_nll"] for x in details)/n,
             "mean_answer_nll_after":sum(x["after"]["answer_nll"] for x in details)/n}
    result={"version":"v0.13.28","evaluation":"TRAINING_PAIRS_NOT_INDEPENDENT",
            "base":str(a.base),"candidate":str(a.candidate),
            "production_unchanged":True,"summary":summary,"details":details}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print("report:",a.output)

if __name__=="__main__":main()
