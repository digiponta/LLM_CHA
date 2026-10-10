"""v0.2.33.25 — Frozen-backbone learned pointer-only / pointer-generator comparison.

All copying positions are PREDICTED from learned attention. No gold position or
gold length is supplied at evaluation time. Base Transformer remains frozen.
"""
import argparse,copy,json,random
from pathlib import Path
import torch
from torch import nn
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from algorithmic_copy_generalization_v023320 import make_pools,make_examples

class PointerHead(nn.Module):
    def __init__(self,dimension,mode):
        super().__init__()
        if mode not in ("pointer","hybrid"):raise ValueError(mode)
        self.mode=mode
        self.query=nn.Linear(dimension,dimension,bias=False)
        self.key=nn.Linear(dimension,dimension,bias=False)
        self.eos=nn.Linear(dimension,1)
        self.gate=nn.Linear(dimension,1) if mode=="hybrid" else None
        self.scale=dimension**-.5

    def distribution(self,model,source,history,marker,bos,eos):
        """Return probabilities for source IDs and EOS; hybrid also includes LM.

        A causal forward pass only sees source and already-generated history.
        """
        context=[bos,marker]+source+[marker]+history
        device=next(model.parameters()).device
        with torch.no_grad():
            hidden=model.forward_hidden(torch.tensor([context],device=device))[0]
            last=hidden[-1].detach()
            src=hidden[2:2+len(source)].detach()
            lm=model.lm_head(last).detach() if self.mode=="hybrid" else None
        ptr=(self.key(src)@self.query(last))*self.scale
        pointer_logits=torch.cat([ptr,self.eos(last)])
        pointer_probs=F.softmax(pointer_logits,dim=0)
        vocab_probs=torch.zeros(model.vocab_size,device=device)
        indices=torch.tensor(source+[eos],device=device,dtype=torch.long)
        vocab_probs=vocab_probs.scatter_add(0,indices,pointer_probs)
        if self.mode=="hybrid":
            gate=torch.sigmoid(self.gate(last)).squeeze()
            vocab_probs=gate*vocab_probs+(1-gate)*F.softmax(lm,dim=-1)
        return vocab_probs,pointer_logits

    def loss_for(self,model,source,marker,bos,eos):
        # Teacher-forced content and end-of-copy supervision.
        losses=[]
        pos_losses=[]
        for j in range(len(source)+1):
            truth=source[j] if j<len(source) else eos
            probs,pos_logits=self.distribution(model,source,source[:j],marker,bos,eos)
            losses.append(-torch.log(probs[truth].clamp_min(1e-10)))
            pos_losses.append(F.cross_entropy(pos_logits.unsqueeze(0),
                              torch.tensor([j],device=pos_logits.device)))
        # Pointer position supervision is a TRAINING label, not an inference oracle.
        return torch.stack(losses).mean()+.15*torch.stack(pos_losses).mean()

def predict(model,head,source,marker,bos,eos,budget=50):
    model.eval();head.eval()
    out=[]
    with torch.inference_mode():
        for _ in range(budget):
            prob,_=head.distribution(model,source,out,marker,bos,eos)
            nxt=int(prob.argmax())
            out.append(nxt)
            if nxt==eos:break
    return out

def evaluate(model,head,examples,marker,bos,eos):
    rows=[]
    for source in examples:
        obtained=predict(model,head,source,marker,bos,eos,max(32,len(source)+5))
        rows.append({"source_ids":source,"generated_ids":obtained,
                     "exact":obtained==source+[eos]})
    return {"exact":sum(r["exact"] for r in rows),"total":len(rows),
            "cases":rows}

def fit_head(model,mode,train,val,marker,bos,eos,epochs,lr,seed):
    torch.manual_seed(seed)
    head=PointerHead(model.d_model,mode).to(next(model.parameters()).device)
    optimizer=torch.optim.AdamW(head.parameters(),lr=lr,weight_decay=.001)
    best=float("inf");best_state=None;best_epoch=0;history=[]
    for epoch in range(1,epochs+1):
        rng=random.Random(seed+epoch)
        order=list(range(len(train)));rng.shuffle(order)
        head.train();total=0.
        for i in order:
            optimizer.zero_grad(set_to_none=True)
            loss=head.loss_for(model,train[i],marker,bos,eos)
            loss.backward()
            nn.utils.clip_grad_norm_(head.parameters(),1.)
            optimizer.step();total+=float(loss.detach())
        head.eval()
        with torch.no_grad():
            v=sum(float(head.loss_for(model,row,marker,bos,eos)) for row in val)/len(val)
        print(f"{mode} epoch={epoch:02d} train={total/len(train):.4f} val={v:.4f}")
        history.append({"epoch":epoch,"train_nll_and_pointer_loss":total/len(train),"val_loss":v})
        if v<best:
            best=v;best_epoch=epoch
            best_state=copy.deepcopy({k:x.detach().cpu() for k,x in head.state_dict().items()})
    head.load_state_dict(best_state)
    return head,history,best_epoch,best

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-algorithmic-copy-v023320.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--epochs",type=int,default=4)
    p.add_argument("--train-count",type=int,default=200)
    p.add_argument("--val-count",type=int,default=40)
    p.add_argument("--test-count",type=int,default=40)
    p.add_argument("--lr",type=float,default=.001)
    p.add_argument("--out",default="results/pointer_copy_v023325.json")
    p.add_argument("--head-dir",default="model/pointer_copy_v023325")
    a=p.parse_args()
    if min(a.epochs,a.train_count,a.val_count,a.test_count)<1 or a.lr<=0:raise ValueError("Invalid options")
    out=Path(a.out);head_dir=Path(a.head_dir)
    if out.exists() or head_dir.exists():raise FileExistsError("Outputs already exist")
    device=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    model,ckpt=LanguageModel.load_checkpoint(a.base,device);model.eval()
    for param in model.parameters():param.requires_grad_(False)
    tok=Tokenizer.load(a.tokenizer)
    if tok.vocab_size!=model.vocab_size:raise ValueError("Tokenizer vocabulary mismatch")
    known,held=make_pools(model.vocab_size)
    marker=ckpt.get("metadata",{}).get("marker_id",7)
    if marker in known+held+[tok.bos_id,tok.eos_id]:raise ValueError("Bad marker")
    data=make_examples(a.seed,known,held,a.train_count,a.val_count,a.test_count)
    # Additional novel token IDs held out from the task's train set.
    novel=list(range(88,104))
    rng=random.Random(a.seed+1000)
    data["novel_extra"]=[[rng.choice(novel) for _ in range(rng.randint(2,8))] for _ in range(40)]
    results={}
    head_dir.mkdir(parents=True,exist_ok=False)
    for mode in ("pointer","hybrid"):
        head,history,epoch,best=fit_head(model,mode,data["train"],data["val"],marker,
            tok.bos_id,tok.eos_id,a.epochs,a.lr,a.seed)
        summaries={}
        for key,examples in data.items():
            summaries[key]=evaluate(model,head,examples,marker,tok.bos_id,tok.eos_id)
            print(f"{mode} {key}: {summaries[key]['exact']}/{summaries[key]['total']}")
        torch.save({"version":"v0.2.33.25","mode":mode,
                    "base_checkpoint":a.base,"state_dict":head.state_dict(),
                    "dim":model.d_model,"epoch":epoch,"best_val_loss":best},
                   head_dir/(mode+".pt"))
        results[mode]={"best_epoch":epoch,"best_val_loss":best,
                       "history":history,"groups":summaries}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"version":"v0.2.33.25","base":a.base,
        "base_frozen":True,"results":results,
        "limitations":["Pointer source positions are supervised during training but predicted at inference",
            "Frozen base model has prior task exposure; train/val/test series are disjoint",
            "Unseen ID experiments test new task IDs, not necessarily never-seen-pretraining embeddings",
            "EOS predicted autonomously by a trainable pointer endpoint",
            "Single synthetic seed. This is not a semantic generation evaluation",
            "No standalone non-pointer retraining control under equal head-training budget"]},
        ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",out,head_dir)
if __name__=="__main__":main()
