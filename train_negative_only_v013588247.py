"""Isolated negative-only unlikelihood experiment. Never promotes to production."""
from __future__ import annotations
import argparse
import copy
import json
import math
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from online_train import ConversationDataset, masked_loss

def read_negative_signals(path):
    found={}
    if not Path(path).exists(): return []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        if not raw.strip():continue
        try: row=json.loads(raw)
        except json.JSONDecodeError:continue
        if row.get("signal")!="NEGATIVE" or row.get("training_status")!="NOT_TRAINED":continue
        q=str(row.get("question","")).strip()
        a=str(row.get("rejected_answer","")).strip()
        if not q or not a:continue
        found[(q,a)]=row
    return list(found.values())

def response_nll(model,x,y,mask):
    return masked_loss(model,x,y,mask)

def unlikelihood_loss(model,x,y,mask):
    # Penalize the conditional likelihood of the full rejected sequence.
    # Bounded derivative w.r.t. sequence log-probability avoids unconstrained ascent CE.
    log_probs=F.log_softmax(model(x),dim=-1).gather(-1,y.unsqueeze(-1)).squeeze(-1)
    seq_logp=((log_probs*mask).sum(dim=-1)/mask.sum(dim=-1).clamp_min(1))
    return F.softplus(seq_logp + 4.0).mean()

def baseline_kl(model,reference,x,mask):
    logits=model(x)
    with torch.no_grad(): base=reference(x)
    p=F.softmax(base,dim=-1)
    kl=(p*(F.log_softmax(base,dim=-1)-F.log_softmax(logits,dim=-1))).sum(dim=-1)
    # Preserve next-token behavior at prompt and rejected-answer positions.
    active=torch.ones_like(mask)
    return (kl*active).sum()/active.sum().clamp_min(1)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--negative-data",default="data/negative_teacher_signals_v013588244.jsonl")
    p.add_argument("--base-model",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="results/negative_only_v013588247.candidate.pt")
    p.add_argument("--report",default="results/negative_only_v013588247.json")
    p.add_argument("--steps",type=int,default=6)
    p.add_argument("--learning-rate",type=float,default=1e-6)
    p.add_argument("--negative-weight",type=float,default=0.05)
    p.add_argument("--kl-weight",type=float,default=1.0)
    p.add_argument("--max-nll-increase",type=float,default=0.35)
    args=p.parse_args()
    if not 1<=args.steps<=100 or not 0<args.learning_rate<=1e-4 or not 0<=args.negative_weight<=1 or not 0<=args.kl_weight<=100:
        raise ValueError("UNSAFE_EXPERIMENT_PARAMETERS")
    rows=read_negative_signals(args.negative_data)
    if not rows:raise SystemExit("NO_NEGATIVE_SIGNAL")
    torch.manual_seed(42)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model,_=LanguageModel.load_checkpoint(args.base_model,device=device)
    reference=copy.deepcopy(model).eval()
    for param in reference.parameters():param.requires_grad_(False)
    tok=Tokenizer.load(args.tokenizer)
    dataset=ConversationDataset([(r["question"],r["rejected_answer"]) for r in rows],tok,model.context_length)
    items=[tuple(z.unsqueeze(0).to(device) for z in dataset[i]) for i in range(len(dataset))]
    model.eval()
    with torch.no_grad():
        before=[float(response_nll(model,*batch).item()) for batch in items]
    opt=torch.optim.AdamW(model.parameters(),lr=args.learning_rate,weight_decay=0)
    for step in range(args.steps):
        x,y,mask=items[step%len(items)]
        model.train()
        opt.zero_grad(set_to_none=True)
        loss=args.negative_weight*unlikelihood_loss(model,x,y,mask)+args.kl_weight*baseline_kl(model,reference,x,mask)
        if not torch.isfinite(loss):raise RuntimeError("NONFINITE_LOSS")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(),0.1)
        opt.step()
    model.eval()
    with torch.no_grad():
        after=[float(response_nll(model,*batch).item()) for batch in items]
    delta=[a-b for a,b in zip(after,before)]
    mean_delta=sum(delta)/len(delta)
    improved=mean_delta>0
    bounded=max(delta)<=args.max_nll_increase
    # Reports whether rejected responses became less likely.
    # Does not claim that correct generation or general stability is preserved.
    status="CANDIDATE_ONLY" if improved and bounded else "NO_PROMOTION_DIAGNOSTIC"
    report={"status":status,"base_model":args.base_model,"candidate":args.output if status=="CANDIDATE_ONLY" else None,
        "negative_count":len(rows),"steps":args.steps,"learning_rate":args.learning_rate,
        "negative_weight":args.negative_weight,"kl_weight":args.kl_weight,
        "before_negative_nll":before,"after_negative_nll":after,"mean_negative_nll_delta":mean_delta,
        "production_promoted":False,"note":"Negative NLL only; no independent holdout, generation or knowledge retention validation."}
    report_path=Path(args.report)
    report_path.parent.mkdir(parents=True,exist_ok=True)
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if status=="CANDIDATE_ONLY":
        output=Path(args.output)
        output.parent.mkdir(parents=True,exist_ok=True)
        # Experimental candidate: not assigned to chat.py model path.
        model.save_checkpoint(str(output),epoch=0,loss=float(sum(after)/len(after)),
            metadata={"experiment":"negative_only_v013588247","production_promoted":False})
    print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":main()
