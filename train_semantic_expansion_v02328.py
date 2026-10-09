"""Train matched baseline/expanded candidates from the SAME frozen base checkpoint.

Never write to the v0.2.32.6 candidate, to the baseline, or Semantic Memory.
"""
import argparse,json,random
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from train_purpose_sft_v02324 import encode_row,loss_rows
from semantic_memory_expansion_v02328 import load_rows
from prepare_purpose_sft_v02324 import REPLAY

def get_sets(path):
    rows=load_rows(path)
    original=[r for r in rows if r["variant_type"]=="original" and r["review_status"]=="APPROVED"]
    expanded=[r for r in rows if r["review_status"]=="APPROVED"]
    if not original:raise ValueError("No approved original memory records")
    if len(expanded)==len(original):raise ValueError("No reviewed expansions; cannot compare")
    return original,expanded

def train(base,tokenizer,examples,replay,output,device,epochs,lr,head_lr,replay_weight,seed):
    torch.manual_seed(seed);random.seed(seed)
    model,_=LanguageModel.load_checkpoint(base,device)
    pairs=[encode_row(tokenizer,x,model.context_length) for x in examples]
    rp=[encode_row(tokenizer,x,model.context_length) for x in replay]
    opt=torch.optim.AdamW([
      {"params":[p for n,p in model.named_parameters() if n!="lm_head.weight"],"lr":lr},
      {"params":[model.lm_head.weight],"lr":head_lr}],weight_decay=.01)
    history=[]
    for epoch in range(1,epochs+1):
        model.train();order=list(pairs);random.shuffle(order);total=0.
        for x in order:
            opt.zero_grad(set_to_none=True)
            value=loss_rows(model,[x],device)
            objective=value+replay_weight*loss_rows(model,[random.choice(rp)],device) if replay_weight else value
            objective.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
            opt.step();total+=value.detach().item()
        history.append({"epoch":epoch,"train_nll":total/len(order)})
        print(f"{Path(output).name} epoch={epoch} train_nll={history[-1]['train_nll']:.4f}")
    model.save_checkpoint(output,epoch=epochs,loss=history[-1]["train_nll"],
                          metadata={"experiment":"v0.2.32.8","examples":len(examples),
                                    "base":base,"mode":Path(output).stem})
    return history

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--expansion",default="data/semantic_expansion_v02328.jsonl")
    p.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--original-out",default="model/model-llm-cha-memory-original-v02328.pt")
    p.add_argument("--expanded-out",default="model/model-llm-cha-memory-expanded-v02328.pt")
    p.add_argument("--report",default="results/semantic_expansion_train_v02328.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--epochs",type=int,default=8)
    p.add_argument("--lr",type=float,default=5e-6)
    p.add_argument("--head-lr",type=float,default=1e-6)
    p.add_argument("--replay-weight",type=float,default=.25)
    p.add_argument("--seed",type=int,default=42)
    args=p.parse_args()
    if args.epochs<1 or args.lr<=0 or args.head_lr<=0 or args.replay_weight<0:raise ValueError("Invalid hyperparameters")
    paths=[Path(args.base).resolve(),Path(args.original_out).resolve(),Path(args.expanded_out).resolve()]
    if len(set(paths))!=3:raise ValueError("Baseline and candidate paths must all differ")
    if any(x.exists() for x in paths[1:]):raise FileExistsError("Refusing to overwrite existing candidate")
    if not Path(args.base).is_file():raise FileNotFoundError(args.base)
    if Path(args.report).exists():raise FileExistsError(args.report)
    orig,exp=get_sets(args.expansion)
    tokenizer=Tokenizer.load(args.tokenizer)
    device=torch.device("cuda" if args.device=="auto" and torch.cuda.is_available() else "cpu" if args.device=="auto" else args.device)
    data={}
    for name,rows,dest in (("original",orig,args.original_out),("expanded",exp,args.expanded_out)):
        Path(dest).parent.mkdir(parents=True,exist_ok=True)
        data[name]={"count":len(rows),"output":dest,
            "history":train(args.base,tokenizer,rows,REPLAY,dest,device,args.epochs,args.lr,
                            args.head_lr,args.replay_weight,args.seed)}
    report=Path(args.report);report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",report)
if __name__=="__main__":main()
