"""v0.2.32.4 response-only purpose-conditioned SFT.
Frozen base preserved; checkpoint selected by validation NLL.
"""
import argparse,json,random,math,copy
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from prepare_purpose_sft_v02324 import build,validate,REPLAY

def encode_row(tok,row,context_length):
    prompt=tok.encode(row["prompt"],add_bos=True)
    answer=tok.encode(row["answer"],add_eos=True)
    ids=prompt+answer
    if len(ids)>context_length:
        raise ValueError(f'Row {row.get("id","replay")} has {len(ids)} tokens > context {context_length}; do not silently truncate')
    # Token logits at index k predict token at k+1. Mask prompt targets.
    x=torch.tensor(ids[:-1],dtype=torch.long)
    y=torch.tensor(ids[1:],dtype=torch.long)
    y[:max(0,len(prompt)-1)]=-100
    assert (y!=-100).any()
    return x,y

def loss_rows(model,pairs,device):
    terms=[]
    for x,y in pairs:
        logits=model(x.unsqueeze(0).to(device))
        labels=y.to(device).unsqueeze(0)
        terms.append(F.cross_entropy(logits.reshape(-1,logits.shape[-1]),labels.reshape(-1)))
    return torch.stack(terms).mean()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="model/model-llm-cha-purpose-sft-v02324.pt")
    p.add_argument("--report",default="results/purpose_sft_v02324.json")
    p.add_argument("--device",choices=["auto","cpu","cuda"],default="auto")
    p.add_argument("--epochs",type=int,default=8)
    p.add_argument("--lr",type=float,default=0.000005)
    p.add_argument("--head-lr",type=float,default=0.000001)
    p.add_argument("--replay-weight",type=float,default=0.25)
    p.add_argument("--seed",type=int,default=42)
    a=p.parse_args()
    if a.epochs<1 or a.lr<=0 or a.head_lr<=0 or a.replay_weight<0:raise ValueError("Invalid training parameters")
    random.seed(a.seed);torch.manual_seed(a.seed)
    device=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else
                        "cpu" if a.device=="auto" else a.device)
    if not Path(a.model).is_file() or not Path(a.tokenizer).is_file():
        raise FileNotFoundError("Base checkpoint or matching tokenizer not found")
    tok=Tokenizer.load(a.tokenizer)
    model,base=LanguageModel.load_checkpoint(a.model,device)
    if tok.vocab_size!=model.vocab_size:raise ValueError("Vocab mismatch")
    rows=build();manifest=validate(rows)
    training=[encode_row(tok,r,model.context_length) for r in rows["train"]]
    validation=[encode_row(tok,r,model.context_length) for r in rows["val"]]
    replay=[encode_row(tok,{**r,"id":"replay"},model.context_length) for r in REPLAY]
    params=[{"params":[p for n,p in model.named_parameters() if n!="lm_head.weight"],"lr":a.lr},
            {"params":[model.lm_head.weight],"lr":a.head_lr}]
    opt=torch.optim.AdamW(params,weight_decay=0.01)
    @torch.no_grad()
    def score(dataset):
        model.eval()
        return float(loss_rows(model,dataset,device).item())
    base_val=score(validation);base_replay=score(replay)
    best=float("inf");best_epoch=0;history=[]
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    for epoch in range(1,a.epochs+1):
        order=list(training);random.shuffle(order)
        model.train()
        total=0.
        for pair in order:
            opt.zero_grad(set_to_none=True)
            task=loss_rows(model,[pair],device)
            if replay and a.replay_weight:
                replay_pair=random.choice(replay)
                objective=task+a.replay_weight*loss_rows(model,[replay_pair],device)
            else:objective=task
            objective.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
            opt.step();total+=float(task.detach().item())
        val=score(validation);retention=score(replay)
        history.append({"epoch":epoch,"train_nll":total/len(order),
                        "val_nll":val,"replay_nll":retention})
        print(f"epoch={epoch:02} train={total/len(order):.4f} val={val:.4f} replay={retention:.4f}")
        if val<best:
            best=val;best_epoch=epoch
            model.save_checkpoint(str(dest),epoch=epoch,loss=val,
                metadata={"purpose_sft_version":"v0.2.32.4","base_checkpoint":str(a.model),
                          "validation_best_epoch":epoch,"split_manifest":manifest,
                          "prompt_format":"short","replay_weight":a.replay_weight})
    report={"device":str(device),"manifest":manifest,
            "baseline":{"val_nll":base_val,"replay_nll":base_replay},
            "best":{"epoch":best_epoch,"val_nll":best},"epochs":history,
            "checkpoint":str(dest),"test_untouched":True}
    path=Path(a.report);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved:",dest,"Report:",path,"Best val:",best)
    print("NOTE: validation NLL is not free-generation quality or evidence of retained conversations.")
if __name__=="__main__":main()
