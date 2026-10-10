"""v0.2.33.28: relative-position and monotonic pointer ablation.

Relative position uses the *generated history length* (available at inference),
not a gold source position. Monotonic mode uses the last PREDICTED pointer
position during free inference; teacher forcing uses a deterministic step-count
proxy so no gold alignment is injected as an input.
Frozen Transformer, new learned pointer heads, no existing file overwritten.
"""
import argparse,copy,json,random
from pathlib import Path
import torch
from torch import nn
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from adaptive_pointer_length_v023326 import prepare,sequences
from algorithmic_copy_generalization_v023320 import make_pools

MODES=("baseline","relative","monotonic","combined")

class PositionPointer(nn.Module):
    def __init__(self,dim,mode):
        super().__init__()
        if mode not in MODES:raise ValueError(mode)
        self.mode=mode
        self.query=nn.Linear(dim,dim,bias=False)
        self.key=nn.Linear(dim,dim,bias=False)
        self.eos=nn.Linear(dim,1)
        self.scale=dim**-.5
        self.relative_strength=nn.Parameter(torch.tensor(0.0)) if mode in ("relative","combined") else None
        self.monotonic_strength=nn.Parameter(torch.tensor(0.0)) if mode in ("monotonic","combined") else None

    def position_logits(self,model,source,history,marker,bos,last_position=None):
        device=next(model.parameters()).device
        ctx=[bos,marker]+list(source)+[marker]+list(history)
        with torch.no_grad():
            hidden=model.forward_hidden(torch.tensor([ctx],dtype=torch.long,device=device))[0]
            last=hidden[-1].detach()
            src=hidden[2:2+len(source)].detach()
        scores=(self.key(src)@self.query(last))*self.scale
        positions=torch.arange(len(source),device=device,dtype=torch.float32)
        if self.relative_strength is not None:
            # Stronger nonnegative learned bias towards current output step.
            expected_step=len(history)
            scores=scores-F.softplus(self.relative_strength)*torch.abs(positions-expected_step)
        if self.monotonic_strength is not None:
            # At inference, this is previous *predicted* source position.
            # At training, history length - 1 is a deterministic policy proxy,
            # not an injected gold attention-position label.
            previous=max(0,len(history)-1) if last_position is None else last_position
            scores=scores-F.softplus(self.monotonic_strength)*F.relu(
                torch.tensor(float(previous),device=device)-positions)
        return torch.cat([scores,self.eos(last)])

    def loss_for(self,model,source,marker,bos,eos):
        losses=[]
        for j in range(len(source)+1):
            logits=self.position_logits(model,source,source[:j],marker,bos)
            # Position supervision; the model predicts positions at inference.
            losses.append(F.cross_entropy(logits.unsqueeze(0),
                torch.tensor([j],device=logits.device)))
        return torch.stack(losses).mean()

def decode(model,head,source,marker,bos,eos):
    history=[];last_position=None
    with torch.inference_mode():
        for _ in range(max(32,len(source)+5)):
            logits=head.position_logits(model,source,history,marker,bos,last_position)
            index=int(logits.argmax())
            token=eos if index==len(source) else source[index]
            history.append(token)
            if token==eos:break
            last_position=index
    return history

def evaluate(model,head,examples,marker,bos,eos):
    exact=0; correct=0;total=0;eos_hits=0;per_position={}
    for seq in examples:
        actual=decode(model,head,seq,marker,bos,eos)
        exact+=int(actual==seq+[eos])
        with torch.no_grad():
            for j in range(len(seq)+1):
                prediction=int(head.position_logits(model,seq,seq[:j],marker,bos).argmax())
                hit=int(prediction==j)
                correct+=hit;total+=1
                p=per_position.setdefault(str(j),{"correct":0,"total":0})
                p["correct"]+=hit;p["total"]+=1
                if j==len(seq):eos_hits+=hit
    return {"exact":exact,"total":len(examples),"teacher_position_accuracy":correct/total,
            "teacher_eos_accuracy":eos_hits/len(examples),"by_position":per_position}

def train(model,head,stages,validations,marker,bos,eos,lr,seed):
    optimizer=torch.optim.AdamW(head.parameters(),lr=lr,weight_decay=.001)
    checkpoints=[];best=float("inf");state=None;best_stage=0
    for stage,examples in enumerate(stages,1):
        idx=list(range(len(examples)));random.Random(seed+stage).shuffle(idx)
        head.train();loss_sum=0.
        for i in idx:
            optimizer.zero_grad(set_to_none=True)
            loss=head.loss_for(model,examples[i],marker,bos,eos)
            loss.backward()
            nn.utils.clip_grad_norm_(head.parameters(),1.)
            optimizer.step();loss_sum+=float(loss.detach())
        head.eval()
        with torch.no_grad():
            v={}
            for name,rows in validations.items():
                v[name]=sum(float(head.loss_for(model,row,marker,bos,eos)) for row in rows)/len(rows)
        balanced=(v["short"]+v["long"])/2
        checkpoints.append({"stage":stage,"train":loss_sum/len(examples),
                            "validation":v,"balanced":balanced})
        print(f"{head.mode} stage={stage}: train={loss_sum/len(examples):.4f} "
              f"short={v['short']:.4f} long={v['long']:.4f} balanced={balanced:.4f}")
        if balanced<best:
            best=balanced;best_stage=stage
            state={k:x.detach().cpu().clone() for k,x in head.state_dict().items()}
    head.load_state_dict(state)
    return checkpoints,best_stage,best

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
    p.add_argument("--out",default="results/relative_monotonic_pointer_v023328.json")
    p.add_argument("--checkpoint-dir",default="model/relative_monotonic_pointer_v023328")
    a=p.parse_args()
    if min(a.train_count,a.val_count,a.test_count)<1 or a.lr<=0:raise ValueError("Invalid options")
    out=Path(a.out);folder=Path(a.checkpoint_dir)
    if out.exists() or folder.exists():raise FileExistsError("Outputs already exist")
    device=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    model,ckpt=LanguageModel.load_checkpoint(a.base,device)
    model.eval()
    for param in model.parameters():param.requires_grad_(False)
    tok=Tokenizer.load(a.tokenizer)
    if tok.vocab_size!=model.vocab_size:raise ValueError("Tokenizer mismatch")
    known,held=make_pools(tok.vocab_size)
    marker=ckpt.get("metadata",{}).get("marker_id",7)
    data=prepare(a.seed,known,held,a.train_count,a.val_count,a.test_count)
    exclude=[x for rows in data.values() for x in rows]
    long_val=sequences(a.seed+999,known,a.val_count,12,18,exclude)
    validations={"short":data["val"],"long":long_val}
    stages=[data["train_short"],data["train_long"],data["train_long"]]
    folder.mkdir(parents=True)
    results={}
    for name in MODES:
        torch.manual_seed(a.seed)
        head=PositionPointer(model.d_model,name).to(device)
        history,best_stage,best=train(model,head,stages,validations,marker,tok.bos_id,tok.eos_id,a.lr,a.seed)
        scores={}
        for key in ("test","long","unseen_token_ids","mixed_ids","novel_extra"):
            scores[key]=evaluate(model,head,data[key],marker,tok.bos_id,tok.eos_id)
            s=scores[key]
            print(f"{name} {key}: exact={s['exact']}/{s['total']} "
                  f"pos={s['teacher_position_accuracy']:.3f} eos={s['teacher_eos_accuracy']:.3f}")
        checkpoint=folder/(name+".pt")
        torch.save({"version":"v0.2.33.28","head_type":name,"model_state_dict":head.state_dict(),
                    "base_checkpoint":a.base,"best_stage":best_stage,"val_loss":best},checkpoint)
        results[name]={"stages":history,"best_stage":best_stage,
                       "balanced_val_loss":best,"scores":scores}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"version":"v0.2.33.28","base_frozen":True,
        "modes":list(MODES),"results":results,
        "limitations":["Relative bias derives from generated output step; copy of nonsequential targets may not benefit",
            "Monotonic forward bias uses previously predicted position at free inference",
            "Training uses a deterministic history-length proxy, not previous sampled prediction",
            "The pointer positions are supervised in training, never supplied in evaluation",
            "Architectures differ in trainable parameter count; one seed, synthetic task",
            "Balanced long/short validation used for checkpoint choice; tests not used"]},
        ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",out,folder)
if __name__=="__main__":main()
