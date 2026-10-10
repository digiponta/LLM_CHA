"""v0.2.33.31 Explicit Copy Cursor & Pointer State.

Frozen backbone; frozen v0.2.33.28 Combined baseline.
Learned cursor modes train position action (advance/stay/skip/stop), predicting
actions from hidden state + previous predicted position, without a gold index
at inference. Deterministic cursor is a task algorithm ceiling, NOT learning.
"""
import argparse,json,random,copy
from pathlib import Path
import torch
from torch import nn
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from algorithmic_copy_generalization_v023320 import make_pools
from adaptive_pointer_length_v023326 import prepare,sequences
from relative_monotonic_pointer_v023328 import PositionPointer,decode as pointer_decode

class CursorHead(nn.Module):
    def __init__(self,dim,mode):
        super().__init__()
        if mode not in ("learned","cursor_pointer"):raise ValueError(mode)
        self.mode=mode
        self.action=nn.Sequential(nn.Linear(dim+2,dim//2),nn.Tanh(),nn.Linear(dim//2,4))
        if mode=="cursor_pointer":
            self.pointer=PositionPointer(dim,"combined")

    def action_logits(self,model,source,history,previous,marker,bos):
        device=next(model.parameters()).device
        context=[bos,marker]+source+[marker]+history
        with torch.no_grad():
            state=model.forward_hidden(torch.tensor([context],device=device,dtype=torch.long))[0,-1].detach()
        prev_ratio=previous/max(1,len(source))
        hist_ratio=len(history)/max(1,len(source))
        features=torch.tensor([prev_ratio,hist_ratio],device=device,dtype=state.dtype)
        return self.action(torch.cat([state,features]))

    def step_logits(self,model,source,history,previous,marker,bos):
        action=self.action_logits(model,source,history,previous,marker,bos)
        if self.mode=="learned":return action,None
        pointer=self.pointer.position_logits(model,source,history,marker,bos,previous if previous>=0 else None)
        # Additional learned copy-position distribution as a candidate vote.
        return action,pointer

    def loss_for(self,model,source,marker,bos,eos):
        # Index begins before the first position. Actions: 0=advance,
        # 1=stay, 2=skip, 3=stop. In clean identity-copy targets each
        # content token requires "advance", followed by "stop".
        # A separate pointer auxiliary target reduces empty supervision
        # for the pointer branch.
        losses=[]
        for j in range(len(source)+1):
            previous=j-1
            action,pointer=self.step_logits(model,source,source[:j],previous,marker,bos)
            target=3 if j==len(source) else 0
            loss=F.cross_entropy(action[None],torch.tensor([target],device=action.device))
            if pointer is not None:
                loss=loss+.2*F.cross_entropy(pointer[None],torch.tensor([j],device=action.device))
            losses.append(loss)
        return torch.stack(losses).mean()

def decode_cursor(model,head,source,marker,bos,eos,budget=None):
    if head is not None:head.eval()
    limit=max(32,len(source)+5) if budget is None else budget
    previous=-1;out=[];positions=[];actions=[]
    with torch.inference_mode():
        for _ in range(limit):
            if head is None:
                action=3 if previous+1>=len(source) else 0
            else:
                logits,pointer=head.step_logits(model,source,out,previous,marker,bos)
                action=int(logits.argmax())
            if action==3:
                out.append(eos);actions.append(action);positions.append(len(source));break
            # action: advance=+1, stay=0, skip=+2
            candidate=max(0,previous+(1 if action==0 else 0 if action==1 else 2))
            if candidate>=len(source):
                out.append(eos);actions.append(3);positions.append(len(source));break
            if head is not None and head.mode=="cursor_pointer":
                proposed=int(pointer.argmax())
                # Learned gate-free compromise: pointer proposal allowed only
                # within one position of stateful cursor (never inject gold).
                if proposed<len(source) and abs(proposed-candidate)<=1:
                    candidate=proposed
            out.append(source[candidate]);positions.append(candidate);actions.append(action)
            previous=candidate
    return {"output":out,"positions":positions,"actions":actions,
            "exact":out==source+[eos]}

def score(model,head,examples,marker,bos,eos):
    rows=[decode_cursor(model,head,s,marker,bos,eos) for s in examples]
    early=late=missing=correct=0
    for src,row in zip(examples,rows):
        out=row["output"]
        if eos not in out:missing+=1
        else:
            j=out.index(eos)
            if j<len(src):early+=1
            elif j>len(src):late+=1
            else:correct+=1
    return {"exact":sum(r["exact"] for r in rows),"total":len(rows),
            "eos":{"early":early,"correct":correct,"late":late,"missing":missing}}

def fit(model,head,stages,validation,marker,bos,eos,lr,seed):
    opt=torch.optim.AdamW(head.parameters(),lr=lr,weight_decay=.001)
    best=float("inf");best_state=None;best_stage=0;history=[]
    for stage,examples in enumerate(stages,1):
        order=list(range(len(examples)));random.Random(seed+stage).shuffle(order)
        head.train();acc=0.
        for idx in order:
            opt.zero_grad(set_to_none=True)
            loss=head.loss_for(model,examples[idx],marker,bos,eos)
            loss.backward();nn.utils.clip_grad_norm_(head.parameters(),1.)
            opt.step();acc+=float(loss.detach())
        with torch.no_grad():
            v={}
            for name,rows in validation.items():
                v[name]=sum(float(head.loss_for(model,s,marker,bos,eos)) for s in rows)/len(rows)
        balanced=(v["short"]+v["long"])/2
        print(f"{head.mode} stage={stage}: train={acc/len(examples):.4f} balanced={balanced:.4f}")
        history.append({"stage":stage,"train":acc/len(examples),"validation":v,"balanced":balanced})
        if balanced<best:
            best=balanced;best_stage=stage
            best_state={k:p.detach().cpu().clone() for k,p in head.state_dict().items()}
    head.load_state_dict(best_state)
    return history,best_stage,best

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-algorithmic-copy-v023320.pt")
    p.add_argument("--baseline-head",default="model/relative_monotonic_pointer_v023328/combined.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--train-count",type=int,default=200)
    p.add_argument("--val-count",type=int,default=40)
    p.add_argument("--test-count",type=int,default=40)
    p.add_argument("--lr",type=float,default=.001)
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--out",default="results/copy_cursor_v023331.json")
    p.add_argument("--checkpoint-dir",default="model/copy_cursor_v023331")
    a=p.parse_args()
    if min(a.train_count,a.val_count,a.test_count)<1 or a.lr<=0:raise ValueError("Invalid args")
    dest=Path(a.out);folder=Path(a.checkpoint_dir)
    if dest.exists() or folder.exists():raise FileExistsError("Refusing overwrite")
    dev=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    model,ckpt=LanguageModel.load_checkpoint(a.base,dev)
    model.eval()
    for parameter in model.parameters():parameter.requires_grad_(False)
    tokenizer=Tokenizer.load(a.tokenizer)
    if tokenizer.vocab_size!=model.vocab_size:raise ValueError("Vocab mismatch")
    marker=ckpt.get("metadata",{}).get("marker_id",7)
    known,held=make_pools(model.vocab_size)
    data=prepare(a.seed,known,held,a.train_count,a.val_count,a.test_count)
    excluded=[x for rows in data.values() for x in rows]
    longval=sequences(a.seed+999,known,a.val_count,12,18,excluded)
    validation={"short":data["val"],"long":longval}
    stages=[data["train_short"],data["train_long"],data["train_long"]]
    saved=torch.load(a.baseline_head,map_location=dev,weights_only=True)
    if saved.get("head_type")!="combined" or saved.get("base_checkpoint")!=a.base:
        raise ValueError("Baseline checkpoint mismatch")
    baseline=PositionPointer(model.d_model,"combined").to(dev)
    baseline.load_state_dict(saved["model_state_dict"]);baseline.eval()
    folder.mkdir(parents=True,exist_ok=False)
    results={}
    groups=("test","long","unseen_token_ids","mixed_ids","novel_extra")
    for label in ("baseline","deterministic_cursor","learned","cursor_pointer"):
        if label=="baseline":
            results[label]={"groups":{}}
            for group in groups:
                rows=data[group]
                predictions=[pointer_decode(model,baseline,x,marker,tokenizer.bos_id,tokenizer.eos_id) for x in rows]
                results[label]["groups"][group]={"exact":sum(p==s+[tokenizer.eos_id] for p,s in zip(predictions,rows)),
                                                   "total":len(rows)}
        elif label=="deterministic_cursor":
            results[label]={"groups":{key:score(model,None,data[key],marker,tokenizer.bos_id,tokenizer.eos_id)
                                      for key in groups},"oracle_algorithm":True}
        else:
            torch.manual_seed(a.seed)
            head=CursorHead(model.d_model,label).to(dev)
            history,best,loss=fit(model,head,stages,validation,marker,tokenizer.bos_id,tokenizer.eos_id,a.lr,a.seed)
            scores={key:score(model,head,data[key],marker,tokenizer.bos_id,tokenizer.eos_id) for key in groups}
            results[label]={"history":history,"selected_stage":best,
                            "balanced_val_loss":loss,"groups":scores}
            torch.save({"version":"v0.2.33.31","head_type":label,"model_state_dict":head.state_dict(),
                        "base_checkpoint":a.base,"best_stage":best},folder/(label+".pt"))
        print(label,{key:f"{v['exact']}/{v['total']}" for key,v in results[label]["groups"].items()})
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps({"version":"v0.2.33.31","base_frozen":True,"results":results,
        "limitations":["Deterministic cursor is a hand-coded copy algorithm ceiling, NOT learned generalization",
        "Learned action labels on clean identity copies are almost entirely ADVANCE then STOP; this may encode the task directly",
        "Cursor-pointer combines learned cursor and pointer proposal within one index; this task-specific proximity rule is not a general-purpose attention decoder",
        "Training and inference use different cursor-history distributions; rollout robustness is not established",
        "Synthetic one-seed experiment; no semantic comprehension claim"]},
        ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",dest,folder)
if __name__=="__main__":main()
