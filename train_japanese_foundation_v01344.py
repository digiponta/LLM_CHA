"""v0.13.44 Japanese foundation-only causal LM adaptation.

No RPC pairs, no production writes. Train/validation sentences are read from
the approved v0.13.43 corpus outputs; an operator-provided source audit is
required. Default is preflight only; --run performs optimization.
"""
import argparse,hashlib,json,random
from pathlib import Path

def read_lines(path):
    rows=[s.strip() for s in path.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    if not rows:raise ValueError(f"empty corpus: {path}")
    if len(rows)!=len(set(rows)):raise ValueError(f"duplicate sentences in {path}")
    return rows

def verify_corpus(train,val,audit,minimum=1000,allow_demo=False):
    if audit.get("version")!="v0.13.43" or audit.get("split")!="SOURCE_GROUPED":
        raise ValueError("expected grouped v0.13.43 corpus audit")
    assignments=audit.get("assignments",{})
    if not ("train" in assignments.values() and "val" in assignments.values()):
        raise ValueError("source split missing a partition")
    if set(train)&set(val):raise ValueError("train/validation text overlap")
    if audit.get("counts")!={"train":len(train),"val":len(val)}:
        raise ValueError("audit count mismatch")
    if not allow_demo and min(len(train),len(val))<minimum:
        raise ValueError(f"too few sentences for research training; need {minimum} in each split; "
                         "use --allow-demo only for pipeline smoke test")
    return {"train_sentences":len(train),"val_sentences":len(val),
            "source_count":len(audit.get("source_audit",[])),
            "small_demo": min(len(train),len(val))<minimum}

def make_examples(sentences,tokenizer,context_length):
    import torch
    xs=[];ys=[];masks=[]
    for s in sentences:
        seq=tokenizer.encode(s,add_bos=True,add_eos=True)
        if len(seq)<3:continue
        for start in range(0,len(seq)-1,context_length):
            section=seq[start:start+context_length+1]
            if len(section)<2:continue
            x=section[:-1];y=section[1:]
            n=len(x)
            xs.append(x+[tokenizer.pad_id]*(context_length-n))
            ys.append(y+[tokenizer.pad_id]*(context_length-n))
            masks.append([1.]*n+[0.]*(context_length-n))
    if not xs:raise ValueError("tokenization yielded no examples")
    return torch.utils.data.TensorDataset(torch.tensor(xs,dtype=torch.long),
       torch.tensor(ys,dtype=torch.long),torch.tensor(masks,dtype=torch.float32))

def masked_ce(model,x,y,mask):
    import torch.nn.functional as F
    logits=model(x)
    per=F.cross_entropy(logits.reshape(-1,logits.size(-1)),y.reshape(-1),reduction="none").reshape_as(y)
    return (per*mask).sum()/mask.sum().clamp(min=1)

def evaluate(model,loader,device):
    import torch
    model.eval();total=0.;n=0.
    with torch.no_grad():
        for x,y,mask in loader:
            x,y,mask=x.to(device),y.to(device),mask.to(device)
            tokens=float(mask.sum())
            total+=float(masked_ce(model,x,y,mask))*tokens;n+=tokens
    return total/max(n,1.)

def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--corpus-dir",type=Path,default=Path("results/japanese_foundation_corpus_v01343"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/japanese_foundation_candidate_v01344.pt"))
    p.add_argument("--report",type=Path,default=Path("results/japanese_foundation_train_v01344.json"))
    p.add_argument("--epochs",type=int,default=2)
    p.add_argument("--batch-size",type=int,default=8)
    p.add_argument("--lr",type=float,default=1e-5)
    p.add_argument("--seed",type=int,default=1344)
    p.add_argument("--min-per-split",type=int,default=1000)
    p.add_argument("--allow-demo",action="store_true")
    p.add_argument("--run",action="store_true")
    a=p.parse_args()
    if a.epochs<1 or a.batch_size<1 or a.lr<=0 or a.min_per_split<1:p.error("invalid hyperparameters")
    trainfile=a.corpus_dir/"train.txt";valfile=a.corpus_dir/"val.txt";auditfile=a.corpus_dir/"audit.json"
    for f in (trainfile,valfile,auditfile,a.base,a.tokenizer):
        if not f.is_file():p.error(f"missing input: {f}")
    if a.output.resolve() in (a.base.resolve(),a.tokenizer.resolve()):
        p.error("output overlaps protected input")
    if a.output.exists() or a.report.exists():p.error("candidate/report exists, refusing overwrite")
    train=read_lines(trainfile);val=read_lines(valfile)
    audit=json.loads(auditfile.read_text(encoding="utf-8-sig"))
    stats=verify_corpus(train,val,audit,a.min_per_split,a.allow_demo)
    print(json.dumps({"version":"v0.13.44","preflight":"PASS",**stats,"run":a.run},ensure_ascii=False))
    if not a.run:return
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    random.seed(a.seed);torch.manual_seed(a.seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(a.seed)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer=Tokenizer.load(str(a.tokenizer))
    model,_=LanguageModel.load_checkpoint(str(a.base),device=device)
    if tokenizer.vocab_size!=model.vocab_size:raise ValueError("tokenizer/model vocab mismatch")
    context=model.context_length
    train_ds=make_examples(train,tokenizer,context)
    val_ds=make_examples(val,tokenizer,context)
    generator=torch.Generator().manual_seed(a.seed)
    train_loader=torch.utils.data.DataLoader(train_ds,batch_size=a.batch_size,shuffle=True,generator=generator)
    val_loader=torch.utils.data.DataLoader(val_ds,batch_size=a.batch_size,shuffle=False)
    base_nll=evaluate(model,val_loader,device)
    optimizer=torch.optim.AdamW(model.parameters(),lr=a.lr,weight_decay=.01)
    best=float("inf");best_epoch=0;history=[];state=None
    for epoch in range(1,a.epochs+1):
        model.train();loss_sum=0.;batches=0
        for x,y,mask in train_loader:
            x,y,mask=x.to(device),y.to(device),mask.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss=masked_ce(model,x,y,mask)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
            optimizer.step()
            loss_sum+=float(loss.item());batches+=1
        val_nll=evaluate(model,val_loader,device)
        history.append({"epoch":epoch,"train_batch_mean_nll":loss_sum/max(batches,1),"val_nll":val_nll})
        print(json.dumps(history[-1],ensure_ascii=False))
        if val_nll<best:
            best=val_nll;best_epoch=epoch
            state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
    model.load_state_dict(state)
    model.save_checkpoint(str(a.output),epoch=best_epoch,loss=best,
         metadata={"experiment":"JAPANESE_FOUNDATION_ONLY","approval":"EXPERIMENTAL",
                   "base":str(a.base),"production_unchanged":True})
    report={"version":"v0.13.44","status":"EXPERIMENTAL_TRAINING_COMPLETE",
            **stats,"base_val_nll":base_nll,"best_val_nll":best,
            "best_epoch":best_epoch,"history":history,"checkpoint":str(a.output),
            "base":str(a.base),"tokenizer":str(a.tokenizer),"seed":a.seed,
            "fingerprints":{str(f):fingerprint(f) for f in (trainfile,valfile,auditfile,a.base,a.tokenizer)},
            "reserved_test_used":False,"production_unchanged":True,
            "limitations":["No human evaluation of fluency; val NLL is not generated-text quality.",
                           "Source independence from historical checkpoint exposure not proven.",
                           "Demo data is unsuitable for claiming Japanese foundation proficiency."]}
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("report:",a.report)
if __name__=="__main__":main()
