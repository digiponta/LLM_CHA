"""v0.13.58.16 corrected offline replay: canonical dialogue and assistant-only loss.

A: literature-only
B: literature + conversation + knowledge
C: literature + conversation + knowledge + persona

All arms start at identical base checkpoint, share the same number of
optimizer updates, seed, batch size, and learning rate. Sampling weights
are experiment hypotheses, NOT token-balanced. No Wikipedia/network.
Preflight by default; --run is explicit. Never modify source/base files.
"""
import argparse,collections,hashlib,json,random
from pathlib import Path
from audit_offline_replay_v0135810 import read_file
from train_literature_v01355 import prepare as verified_literature
from aligned_replay_examples_v0135816 import make_aligned_examples

WEIGHTS={
 "A":{"literature":1.0},
 "B":{"literature":0.5,"conversation":0.4,"knowledge":0.1},
 "C":{"literature":0.5,"conversation":0.3,"knowledge":0.1,"persona":0.1},
}
DEFAULTS={
 "literature":"results/aozora_789_curated_v01353.txt",
 "literature_audit":"results/aozora_789_delta_audit_v01354.json",
 "conversation":"data/replay_conversation_approved_v013582.jsonl",
 "knowledge":"data/replay_knowledge_approved_v013582.jsonl",
 "persona":"data/replay_persona_approved_v013582.jsonl",
 "base":"model/model-llm-try-nagato-chat-v94.pt",
 "tokenizer":"../LLM_GPU/model/tokenizer-v0.7-bpe.json",
}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def make_plan(arms,domains,slots=120,seed=135811):
    if slots<12 or slots%10:raise ValueError("slots must be >=12 multiple of 10")
    if len(set(arms))!=len(arms) or any(x not in WEIGHTS for x in arms):raise ValueError("bad arms")
    for domain,rows in domains.items():
        if not rows:raise ValueError("empty domain "+domain)
    output={}
    for arm in arms:
        rng=random.Random(seed)
        names=list(WEIGHTS[arm]);counts={}
        remaining=slots
        for name in names[:-1]:
            counts[name]=int(slots*WEIGHTS[arm][name])
            remaining-=counts[name]
        counts[names[-1]]=remaining
        tags=[k for k,n in counts.items() for _ in range(n)]
        rng.shuffle(tags)
        # Shuffle domain order independently per experiment without altering
        # model/RNG initialization or the total number of gradient steps.
        pools={}
        for name in names:
            pool=list(domains[name])
            random.Random(seed+sum(map(ord,name))).shuffle(pool)
            pools[name]=pool
        idx=collections.Counter()
        samples=[]
        for tag in tags:
            pool=pools[tag]
            samples.append((tag,pool[idx[tag]%len(pool)]))
            idx[tag]+=1
        output[arm]=(samples,{"slots":slots,"line_counts":counts,
             "unique_available":{n:len(domains[n]) for n in names},
             "max_exposure_per_line":{n:(counts[n]+len(domains[n])-1)//len(domains[n]) for n in names},
             "sampling_unit":"line not BPE token",
             "optimizer_update_count":"computed from dataset batch count"})
    return output

def parse():
    ap=argparse.ArgumentParser()
    for key,value in DEFAULTS.items():ap.add_argument("--"+key.replace("_","-"),type=Path,default=Path(value))
    ap.add_argument("--arms",nargs="+",choices=["A","B","C"],default=["A","B","C"])
    ap.add_argument("--slots",type=int,default=120)
    ap.add_argument("--epochs",type=int,default=1)
    ap.add_argument("--batch-size",type=int,default=4)
    ap.add_argument("--lr",type=float,default=3e-6)
    ap.add_argument("--seed",type=int,default=135811)
    ap.add_argument("--output-dir",type=Path,default=Path("results/offline_replay_v0135816"))
    ap.add_argument("--full-loss",action="store_true",help="ablation: include user prompt labels")
    ap.add_argument("--run",action="store_true")
    return ap.parse_args()

def main():
    a=parse()
    if a.epochs<1 or a.batch_size<1 or a.lr<=0:raise SystemExit("invalid parameters")
    allpaths={key:getattr(a,key) for key in DEFAULTS}
    used={"literature","literature_audit","base","tokenizer"}
    used|={k for arm in a.arms for k in WEIGHTS[arm]}
    for key in sorted(used):
        path=allpaths[key]
        if not path.is_file():raise SystemExit(f"missing {key}: {path}")
        if any(term in path.name.lower() for term in ("holdout","review","validation","val.txt","test")):
            raise SystemExit(f"protected evaluation data path: {path}")
    if a.output_dir.resolve() in {p.resolve() for p in allpaths.values()}:
        raise SystemExit("output overlaps input")
    corpus_train,corpus_val,corpus_stats=verified_literature(a.literature,a.literature_audit)
    domains={"literature":corpus_train}
    for domain in ("conversation","knowledge","persona"):
        if domain in used:domains[domain]=read_file(allpaths[domain])
    seen={}
    for domain,rows in domains.items():
        for line in rows:
            value=" ".join(line.split())
            if value in seen and seen[value]!=domain:
                raise SystemExit(f"cross-domain exact overlap: {domain} vs {seen[value]}")
            seen[value]=domain
    plans=make_plan(a.arms,domains,a.slots,a.seed)
    a.output_dir.mkdir(parents=True,exist_ok=True) if a.run else None
    report={"version":"v0.13.58.16","status":"PREFLIGHT" if not a.run else "EXPERIMENTAL",
       "network":"DISABLED","dialogue_format":"人: {user}\\nAI: {assistant}","assistant_only_loss":not a.full_loss,"arms":{k:v[1] for k,v in plans.items()},
       "source_sha256":{k:sha(allpaths[k]) for k in sorted(used)},
       "literature":{"train_sentences":len(corpus_train),"same_novel_heldback_sentences":len(corpus_val)},
       "independent_holdout_used":False,"production_promotion_allowed":False,
       "limitations":["Approval of replay examples is not evidence of generalization",
        "Sampling unit is line, not token; quality and tokens may differ",
        "Literature diagnostic split shares the same source and may have historical model exposure"]}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not a.run:return
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from train_japanese_foundation_v01344 import masked_ce
    tok=Tokenizer.load(str(a.tokenizer))
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    for arm in a.arms:
        checkpoint=a.output_dir/f"candidate_{arm}.pt"
        if checkpoint.exists():raise SystemExit(f"refusing overwrite: {checkpoint}")
    histories={}
    for arm in a.arms:
        random.seed(a.seed);torch.manual_seed(a.seed)
        if torch.cuda.is_available():torch.cuda.manual_seed_all(a.seed)
        model,_=LanguageModel.load_checkpoint(str(a.base),device=device)
        if model.vocab_size!=tok.vocab_size:raise ValueError("tokenizer/model mismatch")
        mixed,stats=plans[arm]
        ds=make_aligned_examples(mixed,tok,model.context_length,assistant_only=not a.full_loss)
        generator=torch.Generator().manual_seed(a.seed)
        loader=torch.utils.data.DataLoader(ds,batch_size=a.batch_size,shuffle=True,generator=generator)
        opt=torch.optim.AdamW(model.parameters(),lr=a.lr,weight_decay=.01)
        hist=[]
        for epoch in range(1,a.epochs+1):
            model.train();weighted=0.;total=0.;updates=0
            for x,y,mask in loader:
                x,y,mask=x.to(device),y.to(device),mask.to(device)
                opt.zero_grad(set_to_none=True)
                loss=masked_ce(model,x,y,mask);loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
                opt.step()
                weight=float(mask.sum().item())
                weighted+=float(loss.detach().item())*weight;total+=weight;updates+=1
            row={"arm":arm,"epoch":epoch,"train_nll":weighted/max(total,1.),
                 "observed_train_tokens":int(total),"optimizer_updates":updates}
            hist.append(row);print(json.dumps(row,ensure_ascii=False))
        model.save_checkpoint(str(a.output_dir/f"candidate_{arm}.pt"),epoch=a.epochs,
           loss=hist[-1]["train_nll"],
           metadata={"experiment":"ALIGNED_REPLAY_V0135816","arm":arm,
                     "approval":"EXPERIMENTAL","assistant_only_loss":not a.full_loss,"production_unchanged":True})
        histories[arm]=hist
        del opt,model,loader,ds
        if torch.cuda.is_available():torch.cuda.empty_cache()
    report["status"]="EXPERIMENTAL_TRAINING_COMPLETE";report["history"]=histories
    report["training_completed"]=True;report["quality_gate_run"]=False
    dest=a.output_dir/"report.json"
    if dest.exists():raise SystemExit(f"refusing overwrite: {dest}")
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("report:",dest)
if __name__=="__main__":main()
