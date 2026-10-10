"""v0.2.33.20: algorithmic token-ID copying, controlled synthetic evaluation.

The model is trained with a token-level marker protocol rather than natural
language templates, so Unicode/BPE decoding cannot masquerade as token-copy
success. Held-out token IDs and longer sequences are evaluated only after
checkpoint selection. Existing checkpoints are not modified.
"""
import argparse,json,random,hashlib
from pathlib import Path
import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer

def make_pools(vocab_size,known_count=64,held_count=16):
    # Avoid reserved special token IDs (typically PAD,UNK,BOS,EOS = 0..3).
    if vocab_size < known_count+held_count+8:raise ValueError("Vocabulary too small")
    known=list(range(8,8+known_count))
    held=list(range(8+known_count,8+known_count+held_count))
    return known,held

def make_examples(seed,known,held,n_train=400,n_val=80,n_test=80):
    if min(n_train,n_val,n_test)<1:raise ValueError("Empty split")
    rng=random.Random(seed)
    used=set()
    def sample(pool,count,lo,hi):
        out=[]
        while len(out)<count:
            sequence=tuple(rng.choice(pool) for _ in range(rng.randint(lo,hi)))
            if sequence in used:continue
            used.add(sequence);out.append(list(sequence))
        return out
    train=sample(known,n_train,2,8)
    val=sample(known,n_val,2,8)
    test=sample(known,n_test,2,8)
    long=sample(known,40,12,18)
    unseen=sample(held,40,2,8)
    mixed=sample(known+held,40,2,8)
    return {"train":train,"val":val,"test":test,"long":long,
            "unseen_token_ids":unseen,"mixed_ids":mixed}

def encode_pair(seq,marker,bos,eos,context_length):
    # Training text is: BOS,marker,source,marker,source,EOS.
    # Target masking starts with first copied token (after second marker).
    ids=[bos,marker]+seq+[marker]+seq+[eos]
    first_answer_position=len(seq)+3
    if len(ids)>context_length:raise ValueError("Sequence too long for context")
    x=torch.tensor(ids[:-1],dtype=torch.long)
    y=torch.tensor(ids[1:],dtype=torch.long)
    y[:first_answer_position-1]=-100
    return x,y

def generation(model,seq,marker,bos,eos,budget):
    model.eval()
    inp=[bos,marker]+seq+[marker]
    with torch.inference_mode():
        generated=model.generate(inp,max_new_tokens=budget,eos_id=eos,temperature=0,
                                repetition_penalty=1.)
    got=generated[len(inp):]
    expected=seq+[eos]
    run=0
    for a,b in zip(got,expected):
        if a!=b:break
        run+=1
    return {"exact":got==expected,"prefix_correct":run,
            "expected_len":len(expected),"generated_len":len(got),
            "expected_ids":expected,"generated_ids":got}

def evaluate(model,examples,marker,bos,eos,budget):
    cases=[{"input_ids":x,**generation(model,x,marker,bos,eos,budget)} for x in examples]
    return {"correct":sum(x["exact"] for x in cases),"total":len(cases),
            "accuracy":sum(x["exact"] for x in cases)/len(cases),"cases":cases}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-llm-cha-general-copy-v023316.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="model/model-llm-cha-algorithmic-copy-v023320.pt")
    p.add_argument("--report",default="results/algorithmic_copy_v023320.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--train-count",type=int,default=400)
    p.add_argument("--val-count",type=int,default=80)
    p.add_argument("--test-count",type=int,default=80)
    p.add_argument("--epochs",type=int,default=6)
    p.add_argument("--lr",type=float,default=5e-5)
    p.add_argument("--head-lr",type=float,default=1e-5)
    a=p.parse_args()
    if a.epochs<1 or a.lr<=0 or a.head_lr<=0:raise ValueError("Invalid training parameters")
    if Path(a.output).exists() or Path(a.report).exists():raise FileExistsError("Outputs already exist")
    random.seed(a.seed);torch.manual_seed(a.seed)
    dev=torch.device("cuda" if a.device=="auto" and torch.cuda.is_available() else "cpu" if a.device=="auto" else a.device)
    tokenizer=Tokenizer.load(a.tokenizer)
    model,_=LanguageModel.load_checkpoint(a.base,dev)
    if model.vocab_size!=tokenizer.vocab_size:raise ValueError("Vocab mismatch")
    known,held=make_pools(model.vocab_size)
    special={tokenizer.pad_id,tokenizer.unk_id,tokenizer.bos_id,tokenizer.eos_id}
    if set(known+held)&special:raise ValueError("Token pools include special token")
    # Reuse UNK as marker is dangerous: avoid introducing an untrained token
    # by explicitly choosing an ordinary vocabulary token not in data pools.
    marker=7
    if marker in special or marker in known or marker in held:raise ValueError("Bad marker")
    data=make_examples(a.seed,known,held,a.train_count,a.val_count,a.test_count)
    training=[encode_pair(x,marker,tokenizer.bos_id,tokenizer.eos_id,model.context_length) for x in data["train"]]
    validation=[encode_pair(x,marker,tokenizer.bos_id,tokenizer.eos_id,model.context_length) for x in data["val"]]
    opt=torch.optim.AdamW([
        {"params":[p for n,p in model.named_parameters() if n!="lm_head.weight"],"lr":a.lr},
        {"params":[model.lm_head.weight],"lr":a.head_lr}],weight_decay=.01)
    best=float("inf");best_epoch=0;best_state=None;history=[]
    for epoch in range(1,a.epochs+1):
        indices=list(range(len(training)));random.shuffle(indices)
        model.train();total=0.
        for idx in indices:
            x,y=training[idx];x=x[None].to(dev);y=y.to(dev)
            opt.zero_grad(set_to_none=True)
            pred=model(x)[0]
            loss=F.cross_entropy(pred,y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
            opt.step()
            total+=float(loss.detach())
        model.eval()
        with torch.inference_mode():
            values=[]
            for x,y in validation:
                pred=model(x[None].to(dev))[0]
                values.append(float(F.cross_entropy(pred,y.to(dev))))
            val_loss=sum(values)/len(values)
        print(f"epoch={epoch:02d} train={total/len(training):.4f} val={val_loss:.4f}")
        history.append({"epoch":epoch,"train_nll":total/len(training),"val_nll":val_loss})
        if val_loss<best:
            best=val_loss;best_epoch=epoch
            best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
    model.load_state_dict(best_state);model.eval()
    groups={k:evaluate(model,v,marker,tokenizer.bos_id,tokenizer.eos_id,32) for k,v in data.items()}
    for name,v in groups.items():print(f"{name}: {v['correct']}/{v['total']}")
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    model.save_checkpoint(a.output,epoch=best_epoch,loss=best,metadata={
        "version":"v0.2.33.20","synthetic_token_copy":True,"marker_id":marker,
        "known_token_ids":known,"heldout_token_ids":held,"experimental_only":True})
    report={"version":"v0.2.33.20","best_epoch":best_epoch,"best_val_nll":best,
       "token_ids":{"marker":marker,"known":known,"heldout":held},
       "history":history,"groups":groups,"training_set_size":len(training),
       "limitations":["Exact copying here is token-ID fidelity, not natural-language comprehension",
          "Held-out token IDs are not trained as task answers, but the base checkpoint may have seen them in pretraining",
          "Long sequences and new token IDs are held aside from checkpoint selection",
          "Single seed, finite model and synthetic task"],
       "promotion_eligible":False}
    rp=Path(a.report);rp.parent.mkdir(parents=True,exist_ok=True)
    rp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved",a.output,a.report)
if __name__=="__main__":main()
