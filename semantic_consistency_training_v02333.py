"""v0.2.33.3 contrastive semantic consistency for frozen LLM bridge.

For each reviewed teacher answer, train correct semantics to outperform
incorrect semantics on response-token NLL. Probe with held-out generations.
No semantic generalization or INTERNALIZED claim is automatic.
"""
import argparse,json,random
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from train_purpose_sft_v02324 import encode_row
from semantic_generation_bridge_v02332 import (
    Bridge,DIM,features,bridge_logits,generate,load_train,semantic_vector)
from evaluate_semantic_transfer_v02327 import PROBES,LEGACY,prompt_for

def prepare(tok,rows,limit,device):
    examples=[]
    for row in rows:
        x,y=encode_row(tok,row,limit)
        examples.append((x.unsqueeze(0).to(device),y.to(device),features(row).to(device),
                         tuple(row["canonical"].get("purposes",[])),row["id"]))
    if len({p for _,_,_,p,_ in examples})<2:
        raise ValueError("Need at least two distinct purpose classes for negative sampling")
    return examples

def nll(model,bridge,x,y,semantic):
    scores=bridge_logits(model,bridge,x,semantic.view(1,-1))
    return F.cross_entropy(scores.reshape(-1,scores.shape[-1]),y,ignore_index=-100)

def step_loss(model,bridge,positive,negative,weight=1.,margin=.3):
    x,y,s,_,_=positive
    wrong=negative[2]
    pos=nll(model,bridge,x,y,s)
    neg=nll(model,bridge,x,y,wrong)
    # Correct semantic condition must explain gold answer better than wrong purpose.
    contrast=F.softplus(margin+pos-neg)
    return pos+weight*contrast,pos,neg,contrast

def train_arm(base,tok,examples,steps,lr,seed,consistency_weight,margin,device):
    random.seed(seed);torch.manual_seed(seed)
    model,_=LanguageModel.load_checkpoint(base,device)
    if model.vocab_size!=tok.vocab_size:raise ValueError("Vocabulary mismatch")
    model.eval()
    for p in model.parameters():p.requires_grad_(False)
    bridge=Bridge(model.d_model).to(device)
    prepared=prepare(tok,examples,model.context_length,device)
    optimizer=torch.optim.AdamW(bridge.parameters(),lr=lr,weight_decay=0)
    trace=[]
    for k in range(steps):
        item=prepared[k%len(prepared)]
        alternatives=[r for r in prepared if r[3]!=item[3]]
        neg=alternatives[k%len(alternatives)]
        optimizer.zero_grad(set_to_none=True)
        total,pos,wrong,contrast=step_loss(model,bridge,item,neg,consistency_weight,margin)
        total.backward()
        optimizer.step()
        trace.append({"step":k+1,"positive_nll":float(pos.item()),
                      "incorrect_semantic_nll":float(wrong.item()),
                      "contrastive_loss":float(contrast.item())})
        if k==0 or (k+1)%max(1,steps//8)==0:
            print(f"lambda={consistency_weight:g} step={k+1}/{steps} pos={pos.item():.4f} wrong={wrong.item():.4f} contrast={contrast.item():.4f}")
    model.eval();bridge.eval()
    with torch.no_grad():
        gaps=[]
        for item in prepared:
            wrong=next(r for r in prepared if r[3]!=item[3])
            gaps.append(float((nll(model,bridge,item[0],item[1],wrong[2])-
                               nll(model,bridge,item[0],item[1],item[2])).item()))
    return model,bridge,{"steps":steps,"lambda":consistency_weight,
                        "mean_wrong_minus_correct_nll":sum(gaps)/len(gaps),"trace":trace}

def evaluate(model,tok,bridges,probes,max_new_tokens):
    result=[]
    for item in probes:
        modes={}
        for mode,prompt in (("raw",f"人: {item['user']}\nAI: "),
                            ("short",prompt_for(item))):
            # The probe supplies topic and purposes; there is no student parser.
            purpose=[p.strip() for p in item["purpose"].split(",")]
            semantic=semantic_vector(item["topic"],purpose).to(next(model.parameters()).device)
            modes[mode]={name:generate(model,tok,bridge,prompt,semantic,max_new_tokens)
                         for name,bridge in bridges.items()}
        result.append({"kind":item["kind"],"user":item["user"],"modes":modes,
                       "manual_purpose_fidelity":None,"manual_fluency":None})
    return result

def main():
    a=argparse.ArgumentParser()
    a.add_argument("command",choices=("train","evaluate"))
    a.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    a.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    a.add_argument("--expansion",default="data/semantic_expansion_v02328.jsonl")
    a.add_argument("--baseline",default="model/semantic-consistency-baseline-v02333.pt")
    a.add_argument("--consistency",default="model/semantic-consistency-contrast-v02333.pt")
    a.add_argument("--report",default="results/semantic_consistency_train_v02333.json")
    a.add_argument("--evaluation",default="results/semantic_consistency_eval_v02333.json")
    a.add_argument("--steps",type=int,default=72)
    a.add_argument("--lr",type=float,default=.005)
    a.add_argument("--lambda-semantic",type=float,default=1.)
    a.add_argument("--margin",type=float,default=.3)
    a.add_argument("--max-new-tokens",type=int,default=64)
    a.add_argument("--seed",type=int,default=42)
    a.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    v=a.parse_args()
    if v.steps<=0 or v.lr<=0 or v.lambda_semantic<0 or v.margin<0:raise ValueError("Invalid options")
    device=torch.device("cuda" if v.device=="auto" and torch.cuda.is_available() else "cpu" if v.device=="auto" else v.device)
    tok=Tokenizer.load(v.tokenizer)
    if v.command=="train":
        for name in ("baseline","consistency"):
            if Path(getattr(v,name)).exists():raise FileExistsError(getattr(v,name))
        rows=load_train(v.expansion)
        reports={}
        for name,weight in (("baseline",0.),("consistency",v.lambda_semantic)):
            model,bridge,details=train_arm(v.base,tok,rows,v.steps,v.lr,v.seed,weight,v.margin,device)
            path=Path(getattr(v,name));path.parent.mkdir(parents=True,exist_ok=True)
            torch.save({"bridge_state_dict":bridge.state_dict(),"hidden_size":model.d_model,
                        "semantic_dim":DIM,"base":v.base,"lambda":weight,"steps":v.steps,
                        "version":"v0.2.33.3"},path)
            reports[name]=details
        dest=Path(v.report);dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding="utf-8")
        print("Saved",dest)
    else:
        model,_=LanguageModel.load_checkpoint(v.base,device);model.eval()
        bridges={}
        for name in ("baseline","consistency"):
            path=getattr(v,name)
            ck=torch.load(path,map_location=device,weights_only=True)
            if ck["hidden_size"]!=model.d_model or ck["semantic_dim"]!=DIM:
                raise ValueError("Checkpoint mismatch")
            b=Bridge(model.d_model).to(device)
            b.load_state_dict(ck["bridge_state_dict"]);b.eval()
            bridges[name]=b
        out=evaluate(model,tok,bridges,PROBES,v.max_new_tokens)
        path=Path(v.evaluation);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({"results":out,"promotion_eligible":False,
              "warning":"Previously used exploratory probes, not an untouched holdout. Teacher semantic labels given at inference."},
              ensure_ascii=False,indent=2),encoding="utf-8")
        for r in out:
            print(f"[{r['kind']}]",r["user"])
            for mode,data in r["modes"].items():print(" ",mode,data)
        print("Saved",path)
if __name__=="__main__":main()
