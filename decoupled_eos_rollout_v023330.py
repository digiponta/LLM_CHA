"""v0.2.33.30: decoupled EOS and rollout-corruption comparison.

Frozen original LM backbone. Fresh heads share training examples, split, stages,
optimizers. Gold source-index supervision is TRAINING-only. During free decoding,
all choices (including EOS) are autonomous. The corruption arm uses sampled
model rollout prefixes during training with gold NEXT INDEX at the true step;
this is off-policy recovery supervision, not a principled on-policy policy gradient.
"""
import argparse,copy,json,random
from pathlib import Path
import torch
from torch import nn
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from algorithmic_copy_generalization_v023320 import make_pools
from adaptive_pointer_length_v023326 import prepare,sequences
from relative_monotonic_pointer_v023328 import PositionPointer

MODES=("combined","decoupled","rollout","decoupled_rollout")

class DecoupledHead(PositionPointer):
    def __init__(self,dim,decoupled=False):
        super().__init__(dim,"combined")
        self.decoupled=decoupled
        if decoupled:
            self.stop=nn.Sequential(nn.Linear(dim+1,dim//2),nn.Tanh(),nn.Linear(dim//2,1))
    def position_logits(self,model,source,history,marker,bos,last_position=None):
        logits=super().position_logits(model,source,history,marker,bos,last_position)
        if not self.decoupled:return logits
        device=next(model.parameters()).device
        context=[bos,marker]+source+[marker]+history
        with torch.no_grad():
            final=model.forward_hidden(torch.tensor([context],dtype=torch.long,device=device))[0,-1].detach()
        # EOS is a separate binary head; length ratio is observable input,
        # NOT an oracle output length. The model must learn stop policy.
        progress=torch.tensor([len(history)/max(1,len(source))],device=device,dtype=final.dtype)
        stop_logit=self.stop(torch.cat([final,progress])).reshape(())
        return torch.cat([logits[:-1],stop_logit.unsqueeze(0)])
    def supervised_loss(self,model,source,history,step,marker,bos,eos):
        logits=self.position_logits(model,source,history,marker,bos)
        target=step if step<len(source) else len(source)
        # EOS and position are trained jointly but EOS is separate for decoupled arms.
        return F.cross_entropy(logits.unsqueeze(0),
            torch.tensor([target],device=logits.device))

def rollout_history(model,head,source,marker,bos,eos,limit,rng):
    """Sample a model prefix; returns token history, stops at EOS.

    A partial prefix length is chosen exogenously; all tokens are predicted.
    """
    history=[];last_pos=None
    with torch.inference_mode():
        for _ in range(limit):
            logits=head.position_logits(model,source,history,marker,bos,last_pos)
            # Sample with moderate temperature to encounter plausible errors.
            probs=F.softmax(logits/1.0,dim=0)
            pos=int(torch.multinomial(probs,1))
            token=eos if pos==len(source) else source[pos]
            if token==eos:break
            history.append(token);last_pos=pos
    return history

def training_loss(model,head,source,marker,bos,eos,with_rollout,rng):
    losses=[]
    for j in range(len(source)+1):
        # Teacher forcing remains the primary signal.
        gold_prefix=source[:j]
        losses.append(head.supervised_loss(model,source,gold_prefix,j,marker,bos,eos))
    if with_rollout:
        # Only train with non-EOS model prefixes; align target with prefix
        # length. This mitigates history corruption, but does NOT prove
        # correction after skipped/duplicated source positions.
        for _ in range(2):
            j=rng.randint(1,len(source))
            sampled=rollout_history(model,head,source,marker,bos,eos,j,rng)
            if not sampled:continue
            target=min(len(sampled),len(source))
            losses.append(.5*head.supervised_loss(model,source,sampled,target,marker,bos,eos))
    return torch.stack(losses).mean()

def decode(model,head,source,marker,bos,eos,budget=None):
    output=[];last_pos=None
    limit=max(32,len(source)+5) if budget is None else budget
    with torch.inference_mode():
        for _ in range(limit):
            logits=head.position_logits(model,source,output,marker,bos,last_pos)
            pos=int(logits.argmax())
            token=eos if pos==len(source) else source[pos]
            output.append(token)
            if token==eos:break
            last_pos=pos
    return output

def evaluate(model,head,rows,marker,bos,eos):
    exact=0;teacher_pos=0;teacher_total=0;eos_teacher=0;early=0;late=0;missing=0;correct_stop=0
    for src in rows:
        out=decode(model,head,src,marker,bos,eos)
        exact+=int(out==src+[eos])
        if eos not in out:missing+=1
        else:
            stop=out.index(eos)
            if stop<len(src):early+=1
            elif stop>len(src):late+=1
            else:correct_stop+=1
        with torch.inference_mode():
            for j in range(len(src)+1):
                pos=int(head.position_logits(model,src,src[:j],marker,bos).argmax())
                teacher_pos+=int(pos==j);teacher_total+=1
                if j==len(src):eos_teacher+=int(pos==j)
    return {"exact":exact,"total":len(rows),
        "teacher_position_accuracy":teacher_pos/teacher_total,
        "teacher_eos_accuracy":eos_teacher/len(rows),
        "eos":{"early":early,"correct":correct_stop,"late":late,"missing":missing}}

def fit(model,head,mode,stages,validations,marker,bos,eos,seed,lr):
    optimizer=torch.optim.AdamW(head.parameters(),lr=lr,weight_decay=.001)
    best=float("inf");best_state=None;chosen=None;history=[]
    use_rollout=mode in ("rollout","decoupled_rollout")
    for stage,examples in enumerate(stages,1):
        order=list(range(len(examples)));random.Random(seed+stage).shuffle(order)
        rng=random.Random(seed+stage+1000)
        head.train();t=0.
        for i in order:
            optimizer.zero_grad(set_to_none=True)
            loss=training_loss(model,head,examples[i],marker,bos,eos,use_rollout,rng)
            loss.backward()
            nn.utils.clip_grad_norm_(head.parameters(),1.)
            optimizer.step();t+=float(loss.detach())
        head.eval()
        with torch.no_grad():
            v={}
            for label,examples_val in validations.items():
                v[label]=sum(float(training_loss(model,head,row,marker,bos,eos,False,rng))
                             for row in examples_val)/len(examples_val)
        balanced=(v["short"]+v["long"])/2
        history.append({"stage":stage,"train_loss":t/len(examples),
                        "validation":v,"balanced_validation":balanced})
        print(f"{mode} stage={stage} train={t/len(examples):.4f} "
              f"short={v['short']:.4f} long={v['long']:.4f} balanced={balanced:.4f}")
        if balanced<best:
            best=balanced;chosen=stage
            best_state={k:x.detach().cpu().clone() for k,x in head.state_dict().items()}
    head.load_state_dict(best_state)
    return history,chosen,best

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-algorithmic-copy-v023320.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--train-count",type=int,default=200)
    p.add_argument("--val-count",type=int,default=40)
    p.add_argument("--test-count",type=int,default=40)
    p.add_argument("--lr",type=float,default=.001)
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--out",default="results/decoupled_eos_rollout_v023330.json")
    p.add_argument("--heads-dir",default="model/decoupled_eos_rollout_v023330")
    a=p.parse_args()
    if min(a.train_count,a.val_count,a.test_count)<1 or a.lr<=0:raise ValueError("Invalid options")
    out=Path(a.out);folder=Path(a.heads_dir)
    if out.exists() or folder.exists():raise FileExistsError("Refusing overwrite")
    dev=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    model,ckpt=LanguageModel.load_checkpoint(a.base,dev);model.eval()
    for param in model.parameters():param.requires_grad_(False)
    tok=Tokenizer.load(a.tokenizer)
    if model.vocab_size!=tok.vocab_size:raise ValueError("Tokenizer mismatch")
    known,held=make_pools(model.vocab_size)
    marker=ckpt.get("metadata",{}).get("marker_id",7)
    data=prepare(a.seed,known,held,a.train_count,a.val_count,a.test_count)
    excluded=[row for group in data.values() for row in group]
    long_val=sequences(a.seed+999,known,a.val_count,12,18,excluded)
    validation={"short":data["val"],"long":long_val}
    stages=[data["train_short"],data["train_long"],data["train_long"]]
    folder.mkdir(parents=True,exist_ok=False)
    results={}
    for mode in MODES:
        torch.manual_seed(a.seed)
        head=DecoupledHead(model.d_model,decoupled=(mode in ("decoupled","decoupled_rollout"))).to(dev)
        history,stage,loss=fit(model,head,mode,stages,validation,marker,tok.bos_id,tok.eos_id,a.seed,a.lr)
        groups={}
        for key in ("test","long","unseen_token_ids","mixed_ids","novel_extra"):
            groups[key]=evaluate(model,head,data[key],marker,tok.bos_id,tok.eos_id)
            r=groups[key]
            print(f"{mode} {key}: {r['exact']}/{r['total']} "
                  f"pos={r['teacher_position_accuracy']:.3f} EOS={r['eos']}")
        torch.save({"version":"v0.2.33.30","mode":mode,"best_stage":stage,
                    "base_checkpoint":a.base,"model_state_dict":head.state_dict()},folder/(mode+".pt"))
        results[mode]={"training":history,"selected_stage":stage,
                       "balanced_val_loss":loss,"groups":groups}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"version":"v0.2.33.30","base_frozen":True,"results":results,
        "limitations":["Separate EOS logit still uses input length in a progress feature, observable from source",
          "Rollout corruption uses generated history with gold next-step index (off-policy surrogate), not policy-gradient",
          "The four arms do not have identical optimization loss composition or parameter counts",
          "All source position labels are used for training only, not for free decoding",
          "One random seed and synthetic token copying, not semantic text generation"]},
        ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",out,folder)
if __name__=="__main__":main()
