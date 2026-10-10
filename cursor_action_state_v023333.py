"""v0.2.33.33 — Action state ablation (frozen backbone).

Arms: baseline, last_action, repeat_count, transition_state.
All action decisions learned; no forced task transition in inference.
"""
import argparse,copy,json,random
from pathlib import Path
import torch
from torch import nn
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from algorithmic_copy_generalization_v023320 import make_pools
from cursor_generalization_v023332 import TASKS,instruction_actions,action_position,make_data,ConditionalCursor

MODES=("baseline","last_action","repeat_count","transition_state")

class StatefulCursor(ConditionalCursor):
    def __init__(self,dim,mode):
        super().__init__(dim)
        if mode not in MODES:raise ValueError(mode)
        self.mode=mode
        extra={"baseline":0,"last_action":5,"repeat_count":2,"transition_state":7}[mode]
        if extra:
            self.action=nn.Sequential(nn.Linear(dim+16+3+extra,dim),
                                      nn.Tanh(),nn.Linear(dim,4))
    def logits(self,model,source,history,task,previous,marker,bos,last_action=None,repeat_count=0):
        if self.mode=="baseline":
            return super().logits(model,source,history,task,previous,marker,bos)
        device=next(model.parameters()).device
        ctx=[bos,marker]+source+[marker]+history
        with torch.no_grad():
            h=model.forward_hidden(torch.tensor([ctx],device=device,dtype=torch.long))[0,-1].detach()
        tv=self.task_embedding(torch.tensor(TASKS.index(task),device=device))
        scalar=torch.tensor([previous/max(1,len(source)),len(history)/max(1,len(source)),
            len(source)/20.],device=device,dtype=h.dtype)
        features=[h,tv,scalar]
        if self.mode in ("last_action","transition_state"):
            action_id=4 if last_action is None else last_action
            features.append(F.one_hot(torch.tensor(action_id,device=device),num_classes=5).to(h.dtype))
        if self.mode in ("repeat_count","transition_state"):
            features.append(torch.tensor([min(repeat_count,16)/16.,
                float(repeat_count>0)],device=device,dtype=h.dtype))
        return self.action(torch.cat(features))

    def loss_for(self,model,source,task,marker,bos,eos):
        actions,_=instruction_actions(task,len(source))
        history=[];prev=-1;last=None;repeat=0;losses=[]
        for action in actions:
            scores=self.logits(model,source,history,task,prev,marker,bos,last,repeat)
            losses.append(F.cross_entropy(scores[None],
                torch.tensor([action],device=scores.device)))
            if action==3:break
            pos=action_position(prev,action,len(source))
            repeat=repeat+1 if pos==prev else 0
            history.append(source[pos]);prev=pos;last=action
        return torch.stack(losses).mean()

def generate(model,head,source,task,marker,bos,eos,budget=None):
    budget=max(64,2*len(source)+4) if budget is None else budget
    prev=-1;last=None;repeat=0;history=[];actions=[];positions=[]
    with torch.inference_mode():
        for _ in range(budget):
            action=int(head.logits(model,source,history,task,prev,marker,bos,last,repeat).argmax())
            pos=action_position(prev,action,len(source))
            actions.append(action)
            if pos is None or pos>=len(source):
                history.append(eos);positions.append(None);break
            repeat=repeat+1 if pos==prev else 0
            history.append(source[pos]);positions.append(pos)
            prev=pos;last=action
    return {"output":history,"actions":actions,"positions":positions}

def evaluate(model,head,cases,marker,bos,eos,with_cases=False):
    totals={t:{"exact":0,"total":0,"eos_correct":0,
               "first_action_error":{},"repeat_loop_ge_4":0} for t in TASKS}
    sample=[]
    for task,src in cases:
        acts,pos=instruction_actions(task,len(src))
        gold=[src[i] for i in pos]+[eos]
        result=generate(model,head,src,task,marker,bos,eos)
        r=totals[task];r["total"]+=1
        r["exact"]+=int(result["output"]==gold)
        r["eos_correct"]+=int(eos in result["output"] and
                              result["output"].index(eos)==len(pos))
        error=next((j for j in range(min(len(acts),len(result["actions"])))
                    if acts[j]!=result["actions"][j]),None)
        if error is None and len(acts)!=len(result["actions"]):
            error=min(len(acts),len(result["actions"]))
        key="none" if error is None else str(error)
        r["first_action_error"][key]=r["first_action_error"].get(key,0)+1
        r["repeat_loop_ge_4"]+=int(any(
            all(a==1 for a in result["actions"][j:j+4])
            for j in range(max(0,len(result["actions"])-3))))
        if with_cases:
            sample.append({"task":task,"source":src,"expected_actions":acts,
                           "actual_actions":result["actions"],"exact":result["output"]==gold})
    return {"by_task":totals,"overall":{"exact":sum(r["exact"] for r in totals.values()),
            "total":sum(r["total"] for r in totals.values())},
            **({"cases":sample} if with_cases else {})}

def fit(model,head,training,validation,marker,bos,eos,epochs,lr,seed):
    opt=torch.optim.AdamW(head.parameters(),lr=lr,weight_decay=.001)
    best=float("inf");state=None;best_epoch=0;trace=[]
    for epoch in range(1,epochs+1):
        rows=list(training);random.Random(seed+epoch).shuffle(rows)
        head.train();running=0.
        for task,src in rows:
            opt.zero_grad(set_to_none=True)
            loss=head.loss_for(model,src,task,marker,bos,eos)
            loss.backward();nn.utils.clip_grad_norm_(head.parameters(),1.)
            opt.step();running+=float(loss.detach())
        head.eval()
        with torch.no_grad():
            val=sum(float(head.loss_for(model,s,t,marker,bos,eos))
                for t,s in validation)/len(validation)
        print(f"{head.mode} epoch={epoch} train={running/len(rows):.4f} val={val:.4f}")
        trace.append({"epoch":epoch,"train":running/len(rows),"validation":val})
        if val<best:
            best=val;best_epoch=epoch
            state={k:x.detach().cpu().clone() for k,x in head.state_dict().items()}
    head.load_state_dict(state)
    return trace,best_epoch,best

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-algorithmic-copy-v023320.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--train-count",type=int,default=120)
    p.add_argument("--val-count",type=int,default=30)
    p.add_argument("--test-count",type=int,default=30)
    p.add_argument("--epochs",type=int,default=3)
    p.add_argument("--lr",type=float,default=.001)
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--out",default="results/cursor_action_state_v023333.json")
    p.add_argument("--head-dir",default="model/cursor_action_state_v023333")
    a=p.parse_args()
    if min(a.train_count,a.val_count,a.test_count,a.epochs)<1 or a.lr<=0:raise ValueError("invalid parameters")
    out=Path(a.out);folder=Path(a.head_dir)
    if out.exists() or folder.exists():raise FileExistsError("Outputs already exist")
    dev=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    lm,ckpt=LanguageModel.load_checkpoint(a.base,dev);lm.eval()
    for param in lm.parameters():param.requires_grad_(False)
    tok=Tokenizer.load(a.tokenizer)
    if tok.vocab_size!=lm.vocab_size:raise ValueError("Tokenizer mismatch")
    known,held=make_pools(lm.vocab_size)
    marker=ckpt.get("metadata",{}).get("marker_id",7)
    data=make_data(a.seed,known,held,a.train_count,a.val_count,a.test_count)
    folder.mkdir(parents=True,exist_ok=False)
    results={}
    for mode in MODES:
        torch.manual_seed(a.seed)
        head=StatefulCursor(lm.d_model,mode).to(dev)
        trace,epoch,val=fit(lm,head,data["train"],data["validation"],marker,
                  tok.bos_id,tok.eos_id,a.epochs,a.lr,a.seed)
        groups={}
        for name in ("test","long","unseen","mixed_ids","novel_extra"):
            groups[name]=evaluate(lm,head,data[name],marker,tok.bos_id,tok.eos_id)
            print(mode,name,{k:f"{v['exact']}/{v['total']}"
                  for k,v in groups[name]["by_task"].items()})
        torch.save({"version":"v0.2.33.33","mode":mode,"state_dict":head.state_dict(),
                    "best_epoch":epoch,"base":a.base},folder/(mode+".pt"))
        results[mode]={"training":trace,"best_epoch":epoch,"best_validation":val,
                       "groups":groups}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"version":"v0.2.33.33","frozen_backbone":True,
        "results":results,
        "caveats":["All task rules included in training; holdouts test new token sequences, not new rules",
        "Last action and same-position count are observed model state during inference",
        "No forced STOP or correct action injection during inference",
        "STAY/ADVANCE is defined relative to previous predicted cursor; label errors propagate",
        "No same-parameter-count control, single seed, synthetic token task"]},
        ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",out,folder)
if __name__=="__main__":main()
