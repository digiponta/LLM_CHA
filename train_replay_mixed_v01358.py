"""v0.13.58: experimental four-stream replay mixture for LLM_CHA.

Source-specific UTF-8 text files are required for all four domains.
Default is PRE-FLIGHT only. Never use holdout/review/test files as training.
Ratios control the number of sampled sequences, NOT token proportions.
Validation is diagnostic and same-source; no automatic model promotion.
"""
import argparse,collections,hashlib,json,random
from pathlib import Path

DOMAINS=("literature","foundation","conversation","persona")
WEIGHTS={"literature":40,"foundation":30,"conversation":20,"persona":10}
FORBIDDEN=("holdout","test","review","val.txt","validation","eval")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_rows(path):
    text=path.read_text(encoding="utf-8-sig")
    rows=[x.strip() for x in text.splitlines() if x.strip()]
    if not rows:raise ValueError(f"empty domain: {path}")
    return rows
def prepare(sources,seed=1358,steps_per_epoch=400,allow_small=False):
    if set(sources)!=set(DOMAINS):raise ValueError("four domains are required")
    if steps_per_epoch<10 or steps_per_epoch%10:raise ValueError("steps must be positive multiple of 10")
    paths=[Path(sources[k]) for k in DOMAINS]
    if len(set(p.resolve() for p in paths))!=4:raise ValueError("sources must be distinct")
    rows={}
    for name,p in zip(DOMAINS,paths):
        if any(t in p.name.lower() for t in FORBIDDEN):
            raise ValueError(f"possible evaluation file used for training: {p}")
        rows[name]=read_rows(p)
        if not allow_small and len(rows[name])<100:
            raise ValueError(f"insufficient {name} lines ({len(rows[name])}); override only for smoke tests")
    # Distinct input lines from separate streams are mandatory. This is not
    # enough to prove semantic or historical checkpoint non-exposure.
    seen={}
    for name in DOMAINS:
        for line in rows[name]:
            normalized=" ".join(line.split())
            if normalized in seen and seen[normalized]!=name:
                raise ValueError(f"cross-domain exact overlap: {seen[normalized]} vs {name}")
            seen[normalized]=name
    rng=random.Random(seed)
    slots=[]
    for name in DOMAINS:slots.extend([name]*(steps_per_epoch*WEIGHTS[name]//100))
    rng.shuffle(slots)
    stream={k:iter([]) for k in DOMAINS}
    indices={k:0 for k in DOMAINS}
    mixed=[]
    for domain in slots:
        # Cycle shuffled domain lines; sampling small sources can repeat
        # examples, which is recorded in the report.
        idx=indices[domain]%len(rows[domain])
        mixed.append((domain,rows[domain][idx]))
        indices[domain]+=1
    return mixed,{"domain_source_lines":{k:len(v) for k,v in rows.items()},
                  "domain_sampled":dict(collections.Counter(x[0] for x in mixed)),
                  "sampling_unit":"sentence-or-line (not token-balanced)",
                  "ratios_requested":WEIGHTS,"replay_with_replacement":any(indices[k]>len(rows[k]) for k in DOMAINS),
                  "source_independence_verified":False,"training_approved":False}

def main():
    ap=argparse.ArgumentParser()
    for name in DOMAINS:ap.add_argument("--"+name,type=Path,required=True)
    ap.add_argument("--literature-audit",type=Path,required=True)
    ap.add_argument("--base",type=Path,required=True)
    ap.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    ap.add_argument("--output",type=Path,default=Path("results/replay_candidate_v01358.pt"))
    ap.add_argument("--report",type=Path,default=Path("results/replay_train_v01358.json"))
    ap.add_argument("--steps",type=int,default=400,help="sampling slots per epoch, multiple of 10")
    ap.add_argument("--epochs",type=int,default=1)
    ap.add_argument("--batch-size",type=int,default=4)
    ap.add_argument("--lr",type=float,default=3e-6)
    ap.add_argument("--seed",type=int,default=1358)
    ap.add_argument("--allow-small",action="store_true",help="demo only; relax 100-line per-domain requirement")
    ap.add_argument("--run",action="store_true")
    a=ap.parse_args()
    if a.lr<=0 or a.epochs<1 or a.batch_size<1:ap.error("invalid training parameters")
    paths={name:getattr(a,name) for name in DOMAINS}
    protected=[*paths.values(),a.literature_audit,a.base,a.tokenizer]
    for p in protected:
        if not p.is_file():ap.error(f"missing input: {p}")
    if len({p.resolve() for p in [*protected,a.output,a.report]})!=len(protected)+2:
        ap.error("duplicate input/output paths")
    if a.output.exists() or a.report.exists():ap.error("refusing overwrite")
    delta=json.loads(a.literature_audit.read_text(encoding="utf-8-sig"))
    if delta.get("version")!="v0.13.54" or delta.get("status")!="DIFF_VERIFIED":
        ap.error("literature audit not verified")
    if sha(a.literature)!=delta.get("after_sha256"):
        ap.error("literature source/audit hash mismatch")
    try:mixed,stats=prepare(paths,a.seed,a.steps,a.allow_small)
    except ValueError as e:ap.error(str(e))
    print(json.dumps({"version":"v0.13.58","preflight":"PASS","run":a.run,**stats},ensure_ascii=False))
    if not a.run:return
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from train_japanese_foundation_v01344 import make_examples,masked_ce
    random.seed(a.seed);torch.manual_seed(a.seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(a.seed)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model,_=LanguageModel.load_checkpoint(str(a.base),device=device)
    tok=Tokenizer.load(str(a.tokenizer))
    if tok.vocab_size!=model.vocab_size:raise ValueError("tokenizer/model vocab mismatch")
    # A training sequence is one text line; no holdout is used.
    ds=make_examples([text for _,text in mixed],tok,model.context_length)
    loader=torch.utils.data.DataLoader(ds,batch_size=a.batch_size,shuffle=True,
                                     generator=torch.Generator().manual_seed(a.seed))
    opt=torch.optim.AdamW(model.parameters(),lr=a.lr,weight_decay=.01)
    history=[]
    for epoch in range(1,a.epochs+1):
        model.train();num=0.0;den=0.0
        for x,y,mask in loader:
            x,y,mask=x.to(device),y.to(device),mask.to(device)
            opt.zero_grad(set_to_none=True)
            loss=masked_ce(model,x,y,mask)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
            opt.step()
            n=float(mask.sum());num+=float(loss.detach().item())*n;den+=n
        history.append({"epoch":epoch,"train_nll":num/max(den,1),"train_tokens":den})
        print(json.dumps(history[-1]))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    model.save_checkpoint(str(a.output),epoch=a.epochs,loss=history[-1]["train_nll"],
        metadata={"experiment":"REPLAY_MIXED_V01358","approval":"EXPERIMENTAL","production_unchanged":True})
    result={"version":"v0.13.58","status":"EXPERIMENTAL_TRAINING_COMPLETE",
            **stats,"history":history,"base":str(a.base),"checkpoint":str(a.output),
            "input_sha256":{str(p):sha(p) for p in protected},
            "production_unchanged":True,"independent_holdout_used":False,
            "quality_gate_run":False,"production_promotion_allowed":False,
            "limitations":["Training loss is not conversation quality.",
                           "Ratios balance lines rather than tokens.",
                           "Run v0.13.56 and v0.13.57, plus human/independent evaluation before promotion."]}
    with a.report.open("x",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
    print("report:",a.report)

if __name__=="__main__":main()
