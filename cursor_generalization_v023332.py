"""v0.2.33.32: conditional cursor action-learning generalization study.

Task name is supplied at inference, but correct actions, locations, and output
are not. Task-specific deterministic compiler is TRAINING LABEL and oracle
reference only. Frozen backbone and v0.2.33.31 remain unmodified.
"""
import argparse,copy,json,random
from pathlib import Path
import torch
from torch import nn
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from algorithmic_copy_generalization_v023320 import make_pools
from adaptive_pointer_length_v023326 import sequences

TASKS=("identity","selective","repeat","prefix","mixed")
# Positions are zero based, previous cursor starts at -1.
# action 0: advance +1; 1: stay +0; 2: skip +2; 3: stop
def instruction_actions(task,length):
    if task not in TASKS or length<2:raise ValueError("bad task/length")
    if task=="identity":positions=list(range(length))
    elif task=="selective":positions=list(range(0,length,2))
    elif task=="repeat":positions=[i for i in range(length) for _ in (0,1)]
    elif task=="prefix":positions=list(range((length+1)//2))
    else:
        # mixed: repeat even-position tokens, skip odd-position tokens
        positions=[i for i in range(0,length,2) for _ in (0,1)]
    previous=-1;actions=[]
    for index in positions:
        delta=index-previous
        if delta not in (0,1,2):raise ValueError("unsupported jump")
        actions.append({1:0,0:1,2:2}[delta]);previous=index
    actions.append(3)
    return actions,positions

def action_position(previous,action,n):
    if action==3:return None
    if action not in (0,1,2):raise ValueError(action)
    return max(0,previous+(1 if action==0 else 0 if action==1 else 2))

class ConditionalCursor(nn.Module):
    def __init__(self,dim):
        super().__init__()
        self.task_embedding=nn.Embedding(len(TASKS),16)
        self.action=nn.Sequential(nn.Linear(dim+16+3,dim),
                                  nn.Tanh(),nn.Linear(dim,4))
    def logits(self,model,source,history,task,previous,marker,bos):
        if task not in TASKS:raise ValueError(task)
        device=next(model.parameters()).device
        ids=[bos,marker]+source+[marker]+history
        with torch.no_grad():
            hidden=model.forward_hidden(torch.tensor([ids],device=device,dtype=torch.long))[0,-1].detach()
        task_vec=self.task_embedding(torch.tensor(TASKS.index(task),device=device))
        scalars=torch.tensor([previous/max(1,len(source)),
            len(history)/max(1,len(source)),len(source)/20.0],device=device,dtype=hidden.dtype)
        return self.action(torch.cat([hidden,task_vec,scalars]))

    def loss_for(self,model,source,task,marker,bos,eos):
        actions,positions=instruction_actions(task,len(source))
        losses=[];previous=-1;history=[]
        for action in actions:
            logits=self.logits(model,source,history,task,previous,marker,bos)
            losses.append(F.cross_entropy(logits.unsqueeze(0),
                torch.tensor([action],device=logits.device)))
            if action!=3:
                new=action_position(previous,action,len(source))
                history.append(source[new]);previous=new
        return torch.stack(losses).mean()

def generate(model,head,source,task,marker,bos,eos,budget=64):
    previous=-1;out=[];actions=[];positions=[]
    with torch.inference_mode():
        for _ in range(budget):
            action=int(head.logits(model,source,out,task,previous,marker,bos).argmax())
            actions.append(action)
            pos=action_position(previous,action,len(source))
            if pos is None or pos>=len(source):
                out.append(eos);positions.append(None);break
            positions.append(pos)
            out.append(source[pos]);previous=pos
    return {"output":out,"actions":actions,"positions":positions}

def evaluate(model,head,cases,marker,bos,eos):
    correct=0;action_correct=0;action_count=0;eos_ok=0;details=[]
    for task,src in cases:
        expected_actions,positions=instruction_actions(task,len(src))
        gold=[src[p] for p in positions]+[eos]
        got=generate(model,head,src,task,marker,bos,eos,budget=max(64,2*len(src)+4))
        hit=got["output"]==gold
        correct+=hit
        action_count+=len(expected_actions)
        action_correct+=sum(x==y for x,y in zip(got["actions"],expected_actions))
        eos_ok+=int(eos in got["output"] and got["output"].index(eos)==len(gold)-1)
        details.append({"task":task,"source":src,"expected":gold,"actual":got["output"],
                        "expected_actions":expected_actions,"actual_actions":got["actions"],"exact":hit})
    return {"exact":correct,"total":len(cases),
            "action_prefix_accuracy":action_correct/action_count,
            "correct_eos_timing":eos_ok,"cases":details}

def make_data(seed,known,held,train_count,val_count,test_count):
    # Sequence identity is disjoint across train/val/test; task-conditioned pairs
    # for training are balanced. OOD ID cases are not used in training/validation.
    train_src=sequences(seed+11,known,train_count,2,12)
    val_src=sequences(seed+12,known,val_count,2,12,train_src)
    test_src=sequences(seed+13,known,test_count,2,12,train_src+val_src)
    long_src=sequences(seed+14,known,40,13,18,train_src+val_src+test_src)
    unseen=sequences(seed+15,held,40,2,12)
    mixed=sequences(seed+16,known+held,40,2,12,train_src+val_src+test_src+long_src+unseen)
    novel=sequences(seed+17,list(range(88,104)),40,2,12)
    def pairs(samples):
        return [(t,s) for s in samples for t in TASKS]
    return {"train":pairs(train_src),"validation":pairs(val_src),
      "test":pairs(test_src),"long":pairs(long_src),
      "unseen":pairs(unseen),"mixed_ids":pairs(mixed),"novel_extra":pairs(novel)}

def train(model,head,data,marker,bos,eos,seed,epochs,lr):
    opt=torch.optim.AdamW(head.parameters(),lr=lr,weight_decay=.001)
    rng=random.Random(seed);history=[];best=float("inf");best_state=None;best_epoch=0
    for epoch in range(1,epochs+1):
        examples=list(data["train"]);rng.shuffle(examples)
        head.train();total=0.
        for task,source in examples:
            opt.zero_grad(set_to_none=True)
            loss=head.loss_for(model,source,task,marker,bos,eos)
            loss.backward()
            nn.utils.clip_grad_norm_(head.parameters(),1.)
            opt.step();total+=float(loss.detach())
        head.eval()
        with torch.no_grad():
            valid=sum(float(head.loss_for(model,s,t,marker,bos,eos))
                      for t,s in data["validation"])/len(data["validation"])
        history.append({"epoch":epoch,"train_loss":total/len(examples),"val_loss":valid})
        print(f"epoch={epoch:02d} train={total/len(examples):.4f} val={valid:.4f}")
        if valid<best:
            best=valid;best_epoch=epoch
            best_state={k:v.detach().cpu().clone() for k,v in head.state_dict().items()}
    head.load_state_dict(best_state)
    return history,best_epoch,best

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-algorithmic-copy-v023320.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--train-count",type=int,default=120)
    p.add_argument("--val-count",type=int,default=30)
    p.add_argument("--test-count",type=int,default=30)
    p.add_argument("--epochs",type=int,default=3)
    p.add_argument("--lr",type=float,default=.001)
    p.add_argument("--out",default="results/cursor_generalization_v023332.json")
    p.add_argument("--head",default="model/cursor_generalization_v023332.pt")
    a=p.parse_args()
    if min(a.train_count,a.val_count,a.test_count,a.epochs)<1 or a.lr<=0:raise ValueError("Invalid parameters")
    if Path(a.out).exists() or Path(a.head).exists():raise FileExistsError("Refusing overwrite")
    dev=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    model,ckpt=LanguageModel.load_checkpoint(a.base,dev);model.eval()
    for param in model.parameters():param.requires_grad_(False)
    tok=Tokenizer.load(a.tokenizer)
    if tok.vocab_size!=model.vocab_size:raise ValueError("Tokenizer mismatch")
    known,held=make_pools(model.vocab_size)
    marker=ckpt.get("metadata",{}).get("marker_id",7)
    data=make_data(a.seed,known,held,a.train_count,a.val_count,a.test_count)
    torch.manual_seed(a.seed)
    head=ConditionalCursor(model.d_model).to(dev)
    history,best_epoch,best=train(model,head,data,marker,tok.bos_id,tok.eos_id,
                                  a.seed,a.epochs,a.lr)
    groups={}
    for k in ("test","long","unseen","mixed_ids","novel_extra"):
        groups[k]=evaluate(model,head,data[k],marker,tok.bos_id,tok.eos_id)
        print(k,groups[k]["exact"],"/",groups[k]["total"])
        for task in TASKS:
            cases=[(t,s) for t,s in data[k] if t==task]
            r=evaluate(model,head,cases,marker,tok.bos_id,tok.eos_id)
            print(" ",task,r["exact"],"/",r["total"])
    hp=Path(a.head);hp.parent.mkdir(parents=True,exist_ok=True)
    torch.save({"version":"v0.2.33.32","state_dict":head.state_dict(),
                "base":a.base,"best_epoch":best_epoch,"tasks":TASKS},hp)
    report={"version":"v0.2.33.32","training":history,"best_epoch":best_epoch,
      "validation_loss":best,"groups":groups,
      "limitations":["Task identity explicitly provided at inference; correct source positions/actions are not",
                     "Task rules are fixed and fully represented in training; evaluates new sequences/IDs, not held-out rules",
                     "Deterministic task instruction compiler is an oracle used only for labels and evaluation",
                     "Mixed operations are fixed pattern, not arbitrary language instructions",
                     "No real-world semantic generalization; single-seed synthetic dataset"]}
    op=Path(a.out);op.parent.mkdir(parents=True,exist_ok=True)
    op.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",op,hp)
if __name__=="__main__":main()
