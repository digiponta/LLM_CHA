"""Isolated evidence-aligned negative learning experiment. Never alters production."""
import argparse
import copy
import json
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from evidence_aligned_negative_v013588251 import load_aligned

def encode_aligned(tok,prompt,bad,context):
    p=tok.encode(prompt,add_bos=True)
    a=tok.encode(bad,add_eos=True)
    if len(p)<1 or not a:raise ValueError("EMPTY_SEQUENCE")
    seq=p+a
    # Keep each negative answer token with its actual preceding context.
    xs=[];ys=[]
    for pos in range(len(p),len(seq)):
        xs.append(seq[max(0,pos-context):pos])
        ys.append(seq[pos])
    return xs,ys

def mean_nll(model,encoded):
    xs,ys=encoded
    dev=next(model.parameters()).device
    terms=[]
    for context,target in zip(xs,ys):
        inp=torch.tensor([context],device=dev,dtype=torch.long)
        logits=model(inp)[0,-1,:]
        terms.append(-F.log_softmax(logits,dim=-1)[target])
    return torch.stack(terms).mean()

def step_loss(model,reference,encoded,neg_weight,kl_weight):
    xs,ys=encoded
    dev=next(model.parameters()).device
    neg_terms=[];kl_terms=[]
    for context,target in zip(xs,ys):
        inp=torch.tensor([context],device=dev,dtype=torch.long)
        current=F.log_softmax(model(inp)[0,-1,:],dim=-1)
        with torch.no_grad():baseline=F.log_softmax(reference(inp)[0,-1,:],dim=-1)
        # Smooth bounded unlikelihood for each rejected target token.
        neg_terms.append(F.softplus(current[target]+4))
        kl_terms.append(torch.sum(torch.exp(baseline)*(baseline-current)))
    return neg_weight*torch.stack(neg_terms).mean()+kl_weight*torch.stack(kl_terms).mean()

def run(args):
    rows=load_aligned(args.negative_data)
    if not rows:raise ValueError("NO_ALIGNED_NEGATIVES")
    if not (1<=args.steps<=30 and 0<args.learning_rate<=1e-5 and 0<args.negative_weight<=1 and 0<=args.kl_weight<=20):
        raise ValueError("UNSAFE_PARAMETERS")
    if Path(args.output).resolve()==Path(args.base_model).resolve():raise ValueError("CANNOT_OVERWRITE_BASE")
    torch.manual_seed(42)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model,_=LanguageModel.load_checkpoint(args.base_model,device=device)
    reference=copy.deepcopy(model).eval()
    for p in reference.parameters():p.requires_grad_(False)
    tok=Tokenizer.load(args.tokenizer)
    if tok.vocab_size!=model.vocab_size:raise ValueError("TOKENIZER_MODEL_MISMATCH")
    encoded=[encode_aligned(tok,r["prompt"],r["rejected_answer"],model.context_length) for r in rows]
    model.eval()
    with torch.no_grad():before=[float(mean_nll(model,r)) for r in encoded]
    optimizer=torch.optim.AdamW(model.parameters(),lr=args.learning_rate,weight_decay=0.0)
    for step in range(args.steps):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        loss=step_loss(model,reference,encoded[step%len(encoded)],args.negative_weight,args.kl_weight)
        if not torch.isfinite(loss):raise ValueError("NONFINITE_LOSS")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(),0.1)
        optimizer.step()
    model.eval()
    with torch.no_grad():after=[float(mean_nll(model,r)) for r in encoded]
    delta=[a-b for a,b in zip(after,before)]
    eligible=all(d>0 and d<=args.max_nll_increase for d in delta)
    report={"status":"CANDIDATE_ONLY" if eligible else "NO_PROMOTION_DIAGNOSTIC",
            "negative_count":len(rows),"steps":args.steps,"before_nll":before,"after_nll":after,
            "delta_nll":delta,"base_model":args.base_model,
            "candidate":args.output if eligible else None,"production_promoted":False,
            "limitations":["No independent normal-answer retention or evidence gate validation",
                           "Only aligned negative examples; no positive answer supervision"]}
    path=Path(args.report);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if eligible:
        model.save_checkpoint(args.output,epoch=0,loss=sum(after)/len(after),
                             metadata={"experiment":"evidence_aligned_negative_v013588251","production_promoted":False})
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--negative-data",default="data/negative_evidence_aligned_v013588251.jsonl")
    p.add_argument("--base-model",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",required=True)
    p.add_argument("--output",default="results/evidence_aligned_negative_v013588251.candidate.pt")
    p.add_argument("--report",default="results/evidence_aligned_negative_v013588251.json")
    p.add_argument("--steps",type=int,default=3)
    p.add_argument("--learning-rate",type=float,default=1e-6)
    p.add_argument("--negative-weight",type=float,default=0.05)
    p.add_argument("--kl-weight",type=float,default=1.0)
    p.add_argument("--max-nll-increase",type=float,default=0.35)
    a=p.parse_args()
    print(json.dumps(run(a),ensure_ascii=False))
if __name__=="__main__":main()
