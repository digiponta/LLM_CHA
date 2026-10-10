"""v0.2.33.26: frozen-base pointer length curriculum and confidence-adaptive gate.

Three independent fresh heads: pointer / standard hybrid / adaptive hybrid.
Equal steps and examples, shared short-validation selection. Evaluation supplies
neither gold source positions nor gold output length.
"""
import argparse,copy,json,random
from pathlib import Path
import torch
from torch import nn
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from algorithmic_copy_generalization_v023320 import make_pools,make_examples
from pointer_copy_v023325 import PointerHead,predict,evaluate

def sequences(seed,pool,count,lo,hi,exclude=()):
    rng=random.Random(seed);used={tuple(s) for s in exclude};out=[]
    if count<=0 or lo<1 or hi<lo:raise ValueError("invalid split size/length")
    for _ in range(count):
        for attempt in range(100000):
            s=tuple(rng.choice(pool) for _ in range(rng.randint(lo,hi)))
            if s not in used:break
        else:raise ValueError("insufficient unique sequences")
        used.add(s);out.append(list(s))
    return out

def prepare(seed,known,held,train_count=200,val_count=40,test_count=40):
    # Common independent test sets; no train/validation overlap.
    val=sequences(seed+1,known,val_count,2,8)
    test=sequences(seed+2,known,test_count,2,8,val)
    long=sequences(seed+3,known,40,12,18,val+test)
    unseen=sequences(seed+4,held,40,2,8)
    mixed=sequences(seed+5,known+held,40,2,8,val+test+long+unseen)
    extra=list(range(88,104))
    novel_extra=sequences(seed+6,extra,40,2,8)
    # Constant sample count for all arms, with a 3-stage curriculum.
    train_short=sequences(seed+10,known,train_count,2,8,val+test+long+unseen+mixed+novel_extra)
    train_long=sequences(seed+11,known,train_count,2,18,
                         val+test+long+unseen+mixed+novel_extra+train_short)
    return {"val":val,"test":test,"long":long,"unseen_token_ids":unseen,
            "mixed_ids":mixed,"novel_extra":novel_extra,
            "train_short":train_short,"train_long":train_long}

class AdaptiveHead(PointerHead):
    """Gate observes normalized competition/confidence, not token ID identity."""
    def __init__(self,dim):
        super().__init__(dim,"hybrid")
        self.gate=nn.Sequential(nn.Linear(dim+3,32),nn.Tanh(),nn.Linear(32,1))
    def distribution(self,model,source,history,marker,bos,eos):
        ctx=[bos,marker]+source+[marker]+history
        device=next(model.parameters()).device
        with torch.no_grad():
            h=model.forward_hidden(torch.tensor([ctx],device=device))[0]
            last=h[-1].detach();src=h[2:2+len(source)].detach()
            lm=F.softmax(model.lm_head(last).detach(),dim=-1)
        pos_logits=torch.cat([(self.key(src)@self.query(last))*self.scale,self.eos(last)])
        pos=pos_logits.softmax(0)
        ptr=torch.zeros(model.vocab_size,device=device).scatter_add(
            0,torch.tensor(source+[eos],device=device),pos)
        # Observed confidence and disagreement influence learned gating;
        # gradients can flow into pointer confidence (but not frozen LM).
        lm_max=lm.max().reshape(1)
        ptr_max=ptr.max().reshape(1)
        overlap=(ptr*lm).sum().reshape(1)
        gate=torch.sigmoid(self.gate(torch.cat([last,lm_max,ptr_max,overlap]))).squeeze()
        return gate*ptr+(1-gate)*lm,pos_logits

def position_diagnostics(model,head,examples,marker,bos,eos):
    model.eval();head.eval()
    rows=[]
    with torch.no_grad():
        for seq in examples:
            steps=[]
            for j in range(len(seq)+1):
                _,logits=head.distribution(model,seq,seq[:j],marker,bos,eos)
                pred=int(logits.argmax())
                steps.append({"position":j,"pointer_position_correct":pred==j,
                              "predicted_position":pred,"gold_rank":int((logits>logits[j]).sum())+1,
                              "is_eos":j==len(seq)})
            free=predict(model,head,seq,marker,bos,eos,max(32,len(seq)+5))
            rows.append({"length":len(seq),"free_exact":free==seq+[eos],
                         "teacher_pointer_correct":sum(s["pointer_position_correct"] for s in steps),
                         "teacher_pointer_total":len(steps),
                         "teacher_eos_position_correct":steps[-1]["pointer_position_correct"],
                         "steps":steps})
    correct=sum(r["teacher_pointer_correct"] for r in rows)
    count=sum(r["teacher_pointer_total"] for r in rows)
    return {"teacher_pointer_position_accuracy":correct/count,
            "teacher_eos_position_accuracy":sum(r["teacher_eos_position_correct"] for r in rows)/len(rows),
            "free_exact":sum(r["free_exact"] for r in rows),"total":len(rows),"cases":rows}

def fit(model,head,stages,val,marker,bos,eos,lr,seed):
    optimizer=torch.optim.AdamW(head.parameters(),lr=lr,weight_decay=.001)
    best=float("inf");best_state=None;best_stage=0;trace=[]
    for stage_index,rows in enumerate(stages,1):
        order=list(range(len(rows)));random.Random(seed+stage_index).shuffle(order)
        head.train();running=0.
        for idx in order:
            optimizer.zero_grad(set_to_none=True)
            loss=head.loss_for(model,rows[idx],marker,bos,eos)
            loss.backward();nn.utils.clip_grad_norm_(head.parameters(),1.)
            optimizer.step();running+=float(loss.detach())
        head.eval()
        with torch.no_grad():
            vl=sum(float(head.loss_for(model,s,marker,bos,eos)) for s in val)/len(val)
        trace.append({"stage":stage_index,"train_loss":running/len(rows),"short_val_loss":vl})
        print(f"stage={stage_index} train={running/len(rows):.4f} short_val={vl:.4f}")
        if vl<best:
            best=vl;best_stage=stage_index
            best_state={k:v.detach().cpu().clone() for k,v in head.state_dict().items()}
    head.load_state_dict(best_state)
    return trace,best_stage,best

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
    p.add_argument("--out",default="results/adaptive_pointer_length_v023326.json")
    p.add_argument("--head-dir",default="model/adaptive_pointer_length_v023326")
    args=p.parse_args()
    if min(args.train_count,args.val_count,args.test_count)<1 or args.lr<=0:raise ValueError("Invalid options")
    report=Path(args.out);directory=Path(args.head_dir)
    if report.exists() or directory.exists():raise FileExistsError("Outputs already exist")
    dev=torch.device("cuda" if args.device=="auto" and torch.cuda.is_available() else "cpu" if args.device=="auto" else args.device)
    model,ckpt=LanguageModel.load_checkpoint(args.base,dev)
    model.eval()
    for par in model.parameters():par.requires_grad_(False)
    tok=Tokenizer.load(args.tokenizer)
    if tok.vocab_size!=model.vocab_size:raise ValueError("Vocab mismatch")
    known,held=make_pools(model.vocab_size)
    marker=ckpt.get("metadata",{}).get("marker_id",7)
    splits=prepare(args.seed,known,held,args.train_count,args.val_count,args.test_count)
    stages=[splits["train_short"],splits["train_long"],splits["train_long"]]
    directory.mkdir(parents=True,exist_ok=False)
    results={}
    for label in ("pointer","hybrid","adaptive"):
        torch.manual_seed(args.seed)
        head=(AdaptiveHead(model.d_model) if label=="adaptive" else
              PointerHead(model.d_model,label)).to(dev)
        print(f"=== {label} ===")
        trace,best_stage,best=fit(model,head,stages,splits["val"],marker,tok.bos_id,tok.eos_id,args.lr,args.seed)
        scores={}
        for group in ("test","long","unseen_token_ids","mixed_ids","novel_extra"):
            rows=splits[group]
            freem=evaluate(model,head,rows,marker,tok.bos_id,tok.eos_id)
            position=position_diagnostics(model,head,rows,marker,tok.bos_id,tok.eos_id)
            scores[group]={"free":{"exact":freem["exact"],"total":freem["total"]},
                           "position":position}
            print(f"{label} {group}: free={freem['exact']}/{freem['total']} "
                  f"teacher_pos={position['teacher_pointer_position_accuracy']:.3f} "
                  f"teacher_eos={position['teacher_eos_position_accuracy']:.3f}")
        torch.save({"version":"v0.2.33.26","base":args.base,"head_type":label,
                    "state_dict":head.state_dict(),"best_stage":best_stage,
                    "val_loss":best},directory/(label+".pt"))
        results[label]={"history":trace,"best_stage":best_stage,"best_short_val_loss":best,
                        "scores":scores}
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps({"version":"v0.2.33.26","base_frozen":True,
        "design":"3 identical training stages across heads; short -> length 2..18 -> length 2..18",
        "results":results,
        "limitations":["Evaluation predicts all positions and EOS; no gold positions supplied at inference",
           "Teacher-forced pointer accuracy is not autonomous free accuracy",
           "Same short-validation distribution can prefer an earlier checkpoint",
           "No same-budget no-pointer decoder retraining arm",
           "Three heads differ in parameter counts; not parameter-matched",
           "Single random seed and synthetic token data; no natural language claims"]},
        ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",report,directory)
if __name__=="__main__":main()
