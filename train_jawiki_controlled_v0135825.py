"""v0.13.58.25: controlled W/WR/WRP exploratory training.

Dry-run by default. Explicit --run --acknowledge-unapproved-experiment
creates isolated candidates; NEVER promotes checkpoints or semantic memory.
Same initial checkpoint, seed, optimizer and number of updates per arm.
Article-disjoint validation is diagnostic only, not an independent holdout.
"""
import argparse,hashlib,json,random
from pathlib import Path

ARMS=("W","WR","WRP")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(source,tokenizer,base,output,arms,steps,batch_size,lr,seed):
    if output.exists():raise FileExistsError(output)
    if not arms or len(set(arms))!=len(arms) or any(x not in ARMS for x in arms):
        raise ValueError("invalid arms")
    if steps<1 or batch_size<1 or not 0<lr<=0.001:raise ValueError("invalid hyperparameters")
    manifest_path=source/"manifest.json"
    m=json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if m.get("status")!="BALANCED_STAGED_NOT_APPROVED":raise ValueError("unexpected status")
    # Verify all input outputs even for a single arm.
    pools={}
    for arm in ARMS:
        p=source/(arm+"_balanced.jsonl")
        if sha(p)!=m.get("file_sha256",{}).get(p.name):raise ValueError("data SHA mismatch: "+p.name)
        with p.open(encoding="utf-8-sig") as f:
            rows=[json.loads(line) for line in f if line.strip()]
        if not rows:raise ValueError("empty arm "+arm)
        for row in rows:
            ids=row.get("token_ids");mask=row.get("loss_mask")
            if row.get("approval")!="EXPERIMENT_CANDIDATE_ONLY" or not isinstance(ids,list) or not isinstance(mask,list):
                raise ValueError("bad record: "+arm)
            if not 2<=len(ids)<=513 or len(mask)!=len(ids)-1 or any(type(v)!=int or v not in (0,1) for v in mask):
                raise ValueError("bad mask/length: "+arm)
            if row.get("supervised_tokens")!=sum(mask) or sum(mask)==0:
                raise ValueError("bad supervised count: "+arm)
            if any(type(i)!=int or i<0 for i in ids):raise ValueError("bad token ID")
        pools[arm]=rows
    if not tokenizer.is_file() or not base.is_file():raise FileNotFoundError("model/tokenizer missing")
    if sha(tokenizer)!="4f9c7266c88468d0b0b7789ae2bdba03cbe7103d546b2a64eb57dd34e37fb3fc":
        raise ValueError("tokenizer SHA differs from v0.13.58.22 verified tokenizer")
    from model import LanguageModel
    import torch
    model,_=LanguageModel.load_checkpoint(str(base),device=torch.device("cpu"))
    if model.context_length!=512 or model.vocab_size!=8000:
        raise ValueError("base checkpoint architecture mismatch")
    if any(i>=model.vocab_size for rows in pools.values() for row in rows for i in row["token_ids"]):
        raise ValueError("out of vocabulary ID")
    del model
    report={"version":"v0.13.58.25","status":"DRY_RUN_ONLY",
        "source_manifest_sha256":sha(manifest_path),"checkpoint_sha256":sha(base),
        "tokenizer_sha256":sha(tokenizer),"arms":arms,"optimizer":"AdamW",
        "steps_per_arm":steps,"batch_size":batch_size,"lr":lr,"seed":seed,
        "sampling":"seeded with replacement; supervised token exposure depends on chunk lengths",
        "dataset_counts":{arm:{"chunks":len(pools[arm]),"supervised_tokens":sum(r["supervised_tokens"] for r in pools[arm])} for arm in arms},
        "human_review_approved":False,"independent_holdout_verified":False,
        "production_promotion_allowed":False,"training_performed":False,
        "warnings":["Experimental candidates only; Wikipedia remains unapproved.",
                   "Identical steps do not guarantee identical supervised-token exposure.",
                   "No independent holdout or human quality review."]}
    return report,pools

def run(args):
    report,pools=verify(args.input_dir,args.tokenizer,args.base,args.output_dir,args.arms,args.steps,args.batch_size,args.lr,args.seed)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not args.run:return report
    if not args.acknowledge_unapproved_experiment:
        raise ValueError("explicit --acknowledge-unapproved-experiment required")
    import torch
    import torch.nn.functional as F
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    tok=Tokenizer.load(str(args.tokenizer))
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    args.output_dir.mkdir(parents=True,exist_ok=False)
    histories={}
    try:
        for arm in args.arms:
            random.seed(args.seed);torch.manual_seed(args.seed)
            if torch.cuda.is_available():torch.cuda.manual_seed_all(args.seed)
            model,_=LanguageModel.load_checkpoint(str(args.base),device=device)
            model.train()
            optimizer=torch.optim.AdamW(model.parameters(),lr=args.lr,weight_decay=0.01)
            rng=random.Random(args.seed)
            rows=pools[arm];history=[]
            for step in range(1,args.steps+1):
                batch=[rows[rng.randrange(len(rows))] for _ in range(args.batch_size)]
                x=[];y=[];m=[]
                for r in batch:
                    seq=r["token_ids"];length=len(seq)-1
                    x.append(seq[:-1]+[tok.pad_id]*(512-length))
                    y.append(seq[1:]+[tok.pad_id]*(512-length))
                    m.append(r["loss_mask"]+[0]*(512-length))
                x=torch.tensor(x,device=device,dtype=torch.long)
                y=torch.tensor(y,device=device,dtype=torch.long)
                mask=torch.tensor(m,device=device,dtype=torch.float32)
                logits=model(x)
                if isinstance(logits,tuple):logits=logits[0]
                per=F.cross_entropy(logits.reshape(-1,logits.size(-1)),y.reshape(-1),reduction="none").reshape_as(y)
                loss=(per*mask).sum()/mask.sum().clamp_min(1)
                optimizer.zero_grad(set_to_none=True);loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
                optimizer.step()
                entry={"step":step,"train_nll":float(loss.detach().cpu()),"supervised_tokens":int(mask.sum().item())}
                history.append(entry)
                if step==1 or step==args.steps or step%20==0:
                    print(json.dumps({"arm":arm,**entry},ensure_ascii=False))
            outfile=args.output_dir/("candidate_"+arm+".pt")
            model.save_checkpoint(str(outfile),epoch=1,loss=history[-1]["train_nll"],
                metadata={"experiment":"JAWIKI_V0135825","arm":arm,
                          "approval":"EXPERIMENTAL_ONLY","production_unchanged":True})
            histories[arm]={"updates":len(history),
                "observed_supervised_tokens":sum(x["supervised_tokens"] for x in history),
                "mean_train_nll":sum(x["train_nll"]*x["supervised_tokens"] for x in history)/
                  max(1,sum(x["supervised_tokens"] for x in history)),
                "checkpoint_sha256":sha(outfile),"history":history}
            del optimizer,model
            if torch.cuda.is_available():torch.cuda.empty_cache()
        report["status"]="EXPLORATORY_TRAINING_COMPLETE"
        report["training_performed"]=True
        report["history"]=histories
        (args.output_dir/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        return report
    except Exception:
        # Preserve partial artifacts for diagnosis. Never silently overwrite.
        raise

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input-dir",type=Path,default=Path("results/jawiki_balanced_v0135824"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--base",type=Path,default=Path("model/model-llm-try-nagato-chat-v94.pt"))
    p.add_argument("--output-dir",type=Path,default=Path("results/jawiki_controlled_v0135825"))
    p.add_argument("--arms",nargs="+",default=list(ARMS))
    p.add_argument("--steps",type=int,default=60)
    p.add_argument("--batch-size",type=int,default=4)
    p.add_argument("--lr",type=float,default=3e-6)
    p.add_argument("--seed",type=int,default=135825)
    p.add_argument("--run",action="store_true")
    p.add_argument("--acknowledge-unapproved-experiment",action="store_true")
    a=p.parse_args();run(a)
if __name__=="__main__":main()
