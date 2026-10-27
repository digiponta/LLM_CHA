"""v0.13.55 experimental literature-only continued pretraining.

Uses the reviewed v0.13.53 output and verified v0.13.54 audit.
--run explicitly opts in to training. Diagnostic validation is a contiguous
slice of the SAME novel and must never be reported as independent generalization.
Never modifies the base checkpoint or production files.
"""
import argparse,hashlib,json,random
from pathlib import Path

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def prepare(corpus,audit_path,val_fraction=0.05):
    audit=json.loads(audit_path.read_text(encoding="utf-8-sig"))
    if audit.get("version")!="v0.13.54" or audit.get("status")!="DIFF_VERIFIED":
        raise ValueError("verified v0.13.54 delta audit required")
    if audit.get("after_sha256")!=digest(corpus):
        raise ValueError("corpus SHA256 does not match the verified audit")
    rows=[r.strip() for r in corpus.read_text(encoding="utf-8-sig").splitlines() if r.strip()]
    if len(rows)!=audit.get("sentences_after") or len(rows)<100:
        raise ValueError("sentence count mismatch or insufficient corpus")
    if not (0.01<=val_fraction<=0.20):raise ValueError("val_fraction must be 0.01..0.20")
    n=max(1,int(len(rows)*val_fraction))
    train,val=rows[:-n],rows[-n:]
    return train,val,{"sentences":len(rows),"train_sentences":len(train),
        "diagnostic_val_sentences":len(val),
        "validation_type":"IN_SOURCE_CONTIGUOUS_NONINDEPENDENT",
        "source_independence_verified":False,
        "training_approved":False,
        "historical_exposure_not_excluded":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--corpus",type=Path,default=Path("results/aozora_789_curated_v01353.txt"))
    p.add_argument("--audit",type=Path,default=Path("results/aozora_789_delta_audit_v01354.json"))
    p.add_argument("--base",type=Path,required=True,help="existing local checkpoint; never overwritten")
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/literature_candidate_v01355.pt"))
    p.add_argument("--report",type=Path,default=Path("results/literature_train_v01355.json"))
    p.add_argument("--epochs",type=int,default=1)
    p.add_argument("--batch-size",type=int,default=4)
    p.add_argument("--lr",type=float,default=5e-6)
    p.add_argument("--val-fraction",type=float,default=0.05)
    p.add_argument("--seed",type=int,default=1355)
    p.add_argument("--run",action="store_true",help="explicitly run experimental training")
    a=p.parse_args()
    if a.epochs<1 or a.batch_size<1 or a.lr<=0:p.error("invalid hyperparameters")
    for path in (a.corpus,a.audit,a.base,a.tokenizer):
        if not path.is_file():p.error(f"missing input: {path}")
    if a.output.resolve() in {p.resolve() for p in (a.corpus,a.audit,a.base,a.tokenizer)}:
        p.error("checkpoint output overlaps protected input")
    if a.report.resolve() in {p.resolve() for p in (a.corpus,a.audit,a.base,a.tokenizer,a.output)}:
        p.error("report output overlaps protected input")
    if a.output.exists() or a.report.exists():p.error("output/report exists; refusing overwrite")
    train,val,stats=prepare(a.corpus,a.audit,a.val_fraction)
    print(json.dumps({"version":"v0.13.55","preflight":"PASS",**stats,
                      "run":a.run},ensure_ascii=False))
    if not a.run:return
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from train_japanese_foundation_v01344 import make_examples,masked_ce,evaluate
    random.seed(a.seed);torch.manual_seed(a.seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(a.seed)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(str(a.tokenizer))
    model,_=LanguageModel.load_checkpoint(str(a.base),device=device)
    if model.vocab_size!=tok.vocab_size:raise ValueError("tokenizer/model vocabulary mismatch")
    train_ds=make_examples(train,tok,model.context_length)
    val_ds=make_examples(val,tok,model.context_length)
    train_loader=torch.utils.data.DataLoader(train_ds,batch_size=a.batch_size,shuffle=True,
                                            generator=torch.Generator().manual_seed(a.seed))
    val_loader=torch.utils.data.DataLoader(val_ds,batch_size=a.batch_size,shuffle=False)
    initial=evaluate(model,val_loader,device)
    opt=torch.optim.AdamW(model.parameters(),lr=a.lr,weight_decay=0.01)
    history=[];best=float("inf");best_epoch=0;best_state=None
    for epoch in range(1,a.epochs+1):
        model.train();weighted=0.0;tokens=0.0
        for x,y,mask in train_loader:
            x,y,mask=x.to(device),y.to(device),mask.to(device)
            opt.zero_grad(set_to_none=True)
            loss=masked_ce(model,x,y,mask)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
            opt.step()
            weight=float(mask.sum().item());weighted+=float(loss.item())*weight;tokens+=weight
        diagnostic=evaluate(model,val_loader,device)
        row={"epoch":epoch,"train_nll":weighted/max(tokens,1),"diagnostic_val_nll":diagnostic}
        history.append(row);print(json.dumps(row,ensure_ascii=False))
        if diagnostic<best:
            best=diagnostic;best_epoch=epoch
            best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
    model.load_state_dict(best_state)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    model.save_checkpoint(str(a.output),epoch=best_epoch,loss=best,
        metadata={"experiment":"LITERATURE_CONTINUED_PRETRAIN_V01355",
                  "base":str(a.base),"production_unchanged":True,
                  "validation":"NONINDEPENDENT_IN_SOURCE","approval":"EXPERIMENTAL"})
    result={"version":"v0.13.55","status":"EXPERIMENTAL_TRAINING_COMPLETE",
            **stats,"base_diagnostic_val_nll":initial,
            "best_diagnostic_val_nll":best,"best_epoch":best_epoch,
            "history":history,"checkpoint":str(a.output),"base":str(a.base),
            "tokenizer":str(a.tokenizer),
            "input_sha256":{str(p):digest(p) for p in (a.corpus,a.audit,a.base,a.tokenizer)},
            "production_unchanged":True,"reserved_holdout_used":False,
            "limitations":["Diagnostic validation shares source with training.",
                           "Historical checkpoint may already contain this novel.",
                           "Generation quality/persona preservation require separate comparison."]}
    with a.report.open("x",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=False,indent=2)
    print("report:",a.report)

if __name__=="__main__":main()
