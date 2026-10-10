"""v0.2.33.22 controlled 2x2 sequence-length x token-pool expansion.

Same base checkpoint, update count, random seed, and validation-only selection.
Tests include separate novel IDs excluded from ALL four training conditions.
"""
import argparse,json,random
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from algorithmic_copy_generalization_v023320 import encode_pair,generation

ARMS=(("baseline",8,64),("length",18,64),("vocabulary",8,80),("combined",18,80))
def pools(vocab):
    if vocab<112:raise ValueError("Vocabulary too small")
    return list(range(8,72)),list(range(72,88)),list(range(88,104))
def data_sequences(seed,pool,count,lo,hi,exclusions=()):
    if count<1 or lo<1 or lo>hi:raise ValueError("Invalid dataset request")
    rng=random.Random(seed);used=set(map(tuple,exclusions));output=[]
    for _ in range(count):
        for retry in range(100000):
            t=tuple(rng.choice(pool) for _ in range(rng.randint(lo,hi)))
            if t not in used:break
        else:raise RuntimeError("Unable to generate unique sequences")
        used.add(t);output.append(list(t))
    return output

def prepare(seed,train_count=400,val_count=80,test_count=80):
    known,added,novel=pools(8000)
    # All arms use identical evaluation examples; tests are isolated from
    # training and validation even where the token pool intersects.
    val=data_sequences(seed+900,known,val_count,2,8)
    short=data_sequences(seed+901,known,test_count,2,8,val)
    long=data_sequences(seed+902,known,40,12,18,val+short)
    expanded=data_sequences(seed+903,known+added,40,2,8,val+short+long)
    novel_only=data_sequences(seed+904,novel,40,2,8)
    novel_mix=data_sequences(seed+905,known+added+novel,40,2,8,val+short+long+expanded)
    return dict(val=val,short=short,long=long,expanded=expanded,
                novel_only=novel_only,novel_mix=novel_mix)

def score_teacher(model,rows,device):
    model.eval()
    with torch.inference_mode():
        losses=[]
        for x,y in rows:
            logits=model(x.unsqueeze(0).to(device))[0]
            losses.append(float(F.cross_entropy(logits,y.to(device))))
    return sum(losses)/len(losses)

def eval_group(model,samples,marker,bos,eos):
    by_length={};exact=0
    for seq in samples:
        result=generation(model,seq,marker,bos,eos,max(32,len(seq)+5))
        exact+=int(result["exact"])
        key=str(len(seq))
        row=by_length.setdefault(key,{"correct":0,"total":0})
        row["correct"]+=int(result["exact"]);row["total"]+=1
    return {"correct":exact,"total":len(samples),"accuracy":exact/len(samples),
            "length_breakdown":by_length}

def train_arm(name,max_len,pool,base,tok,device,args,groups,marker):
    torch.manual_seed(args.seed)
    model,_=LanguageModel.load_checkpoint(base,device)
    # Each arm has exactly the same number of examples and optimizer steps.
    # Different source lengths necessarily change token-level workload.
    exclusions=groups["val"]+groups["short"]+groups["long"]+groups["expanded"]+groups["novel_only"]+groups["novel_mix"]
    training=data_sequences(args.seed+100,pool,args.train_count,2,max_len,exclusions)
    rows=[encode_pair(s,marker,tok.bos_id,tok.eos_id,model.context_length) for s in training]
    validation=[encode_pair(s,marker,tok.bos_id,tok.eos_id,model.context_length) for s in groups["val"]]
    optimizer=torch.optim.AdamW([
      {"params":[p for n,p in model.named_parameters() if n!="lm_head.weight"],"lr":args.lr},
      {"params":[model.lm_head.weight],"lr":args.head_lr}],weight_decay=.01)
    best=float("inf");state=None;epoch_best=0;trace=[]
    for epoch in range(1,args.epochs+1):
        rng=random.Random(args.seed+epoch)
        order=list(range(len(rows)));rng.shuffle(order)
        model.train();running=0.
        for idx in order:
            x,y=rows[idx];x=x.unsqueeze(0).to(device);y=y.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss=F.cross_entropy(model(x)[0],y)
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
            optimizer.step();running+=float(loss.detach())
        loss_val=score_teacher(model,validation,device)
        trace.append({"epoch":epoch,"train_nll":running/len(rows),"val_nll":loss_val})
        print(f"{name} epoch={epoch:02d} train={running/len(rows):.4f} val={loss_val:.4f}")
        if loss_val<best:
            best=loss_val;epoch_best=epoch
            state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
    model.load_state_dict(state);model.eval()
    scores={k:eval_group(model,seqs,marker,tok.bos_id,tok.eos_id) for k,seqs in groups.items() if k!="val"}
    scores["training_probe"]=eval_group(model,training[:40],marker,tok.bos_id,tok.eos_id)
    scores["validation"]=eval_group(model,groups["val"],marker,tok.bos_id,tok.eos_id)
    model.save_checkpoint(str(Path(args.model_dir)/(name+".pt")),epoch=epoch_best,loss=best,
          metadata={"version":"v0.2.33.22","arm":name,"experimental_only":True})
    return {"arm":name,"max_train_length":max_len,"train_pool_size":len(pool),
            "best_epoch":epoch_best,"best_val_nll":best,"history":trace,
            "scores":scores,"training_sequences":len(training)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-general-copy-v023316.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--train-count",type=int,default=400)
    p.add_argument("--val-count",type=int,default=80)
    p.add_argument("--test-count",type=int,default=80)
    p.add_argument("--epochs",type=int,default=6)
    p.add_argument("--lr",type=float,default=5e-5)
    p.add_argument("--head-lr",type=float,default=1e-5)
    p.add_argument("--out-dir",default="results/token_copy_factorial_v023322")
    p.add_argument("--model-dir",default="model/token_copy_factorial_v023322")
    a=p.parse_args()
    if min(a.epochs,a.train_count,a.val_count,a.test_count)<1 or a.lr<=0 or a.head_lr<=0:
        raise ValueError("Invalid hyperparameters")
    out=Path(a.out_dir);models=Path(a.model_dir)
    if out.exists() or models.exists():raise FileExistsError("Refusing overwrite")
    random.seed(a.seed);torch.manual_seed(a.seed)
    device=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    tok=Tokenizer.load(a.tokenizer)
    base,_=LanguageModel.load_checkpoint(a.base,device)
    if tok.vocab_size!=base.vocab_size:raise ValueError("Vocabulary mismatch")
    known,added,novel=pools(tok.vocab_size)
    marker=7
    if marker in {tok.bos_id,tok.eos_id,tok.pad_id,tok.unk_id}:
        raise ValueError("Marker collides with special token")
    groups=prepare(a.seed,a.train_count,a.val_count,a.test_count)
    out.mkdir(parents=True);models.mkdir(parents=True)
    results=[]
    for name,maxlen,poolcount in ARMS:
        pool=known+(added if poolcount==80 else [])
        result=train_arm(name,maxlen,pool,a.base,tok,device,a,groups,marker)
        results.append(result)
        print(name, {k:f"{v['correct']}/{v['total']}" for k,v in result["scores"].items()})
        (out/(name+".json")).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf8")
    (out/"summary.json").write_text(json.dumps({"version":"v0.2.33.22",
        "design":"2x2: length <=8 vs <=18; 64 vs 80 train IDs",
        "heldout_id_range":novel,"expanded_id_range":added,
        "notes":["Equal example counts, update counts and initial checkpoint; token workload differs by length",
                 "Validation examples use known IDs length 2-8 for every arm",
                 "Novel IDs 88-103 are held out from every training arm",
                 "Data generated synthetically, one seed only",
                 "Evaluation is token exact including EOS; no semantic claims",
                 "Do not promote an experimental model without independent validation"],
        "results":[{"arm":r["arm"],"best_epoch":r["best_epoch"],
                    "best_val_nll":r["best_val_nll"],"scores":r["scores"]} for r in results]},
        ensure_ascii=False,indent=2),encoding="utf8")
    print("Saved",out/"summary.json")
if __name__=="__main__":main()
