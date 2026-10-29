"""Experimental daily-conversation SFT for the 8.96M LLM, v0.13.58.47.

No automatic production promotion; small synthetic holdout measures only exploratory
generalization. Original checkpoint is never overwritten.
"""
import argparse,hashlib,json,random
from pathlib import Path
from dialogue_format_v0135817 import dialogue_for
from aligned_replay_examples_v0135816 import make_aligned_examples
from train_japanese_foundation_v01344 import masked_ce
from train_iterative_corrective_v0135833 import generate

def checksum(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dataset(path):
    rows=[json.loads(s) for s in path.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    if len({r["id"] for r in rows})!=len(rows):raise ValueError("duplicate IDs")
    for r in rows:
        if r["split"] not in ("train","holdout","protected"):raise ValueError("invalid split")
        if not r["user"] or not r["assistant"]:raise ValueError("empty dialogue")
        if "\ufffd" in r["user"]+r["assistant"]:raise ValueError("replacement character")
    train=[r for r in rows if r["split"]=="train"]
    holdout=[r for r in rows if r["split"]=="holdout"]
    protected=[r for r in rows if r["split"]=="protected"]
    if not train or not holdout or not protected:raise ValueError("missing split")
    if {r["user"] for r in train}&{r["user"] for r in holdout}:raise ValueError("holdout overlap")
    return train,holdout,protected

def evaluate(model,tok,rows,max_tokens):
    model.eval()
    return [{"id":r["id"],"prompt":r["user"],"reference":r["assistant"],
             "generated":generate(model,tok,r,max_tokens)} for r in rows]

def run(args):
    train,holdout,protected=dataset(args.source)
    if args.output_dir.exists():raise FileExistsError(args.output_dir)
    if not (1<=args.steps<=300 and 1<=args.max_new_tokens<=128):raise ValueError("invalid bounds")
    if args.lr<=0 or args.lr>1e-4:raise ValueError("unsafe lr")
    report={"version":"v0.13.58.47","status":"DRY_RUN","source_sha256":checksum(args.source),
            "base_sha256":checksum(args.base),"tokenizer_sha256":checksum(args.tokenizer),
            "counts":{"train":len(train),"holdout":len(holdout),"protected":len(protected)},
            "steps":args.steps,"training_performed":False,"production_promotion_allowed":False,
            "holdout_independent":False,"note":"synthetic holdout; not independently authored"}
    if not args.run:
        print(json.dumps(report,ensure_ascii=False,indent=2));return report
    if not args.acknowledge_experiment:raise ValueError("--acknowledge-experiment required")
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    random.seed(args.seed);torch.manual_seed(args.seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(args.seed)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(str(args.tokenizer))
    model,_=LanguageModel.load_checkpoint(str(args.base),device=device)
    if model.vocab_size!=tok.vocab_size:raise ValueError("tokenizer mismatch")
    before=evaluate(model,tok,holdout+protected,args.max_new_tokens)
    # Protected replay deliberately uses verified baseline model outputs, not invented truths.
    protected_replay=[{"user":r["user"],"assistant":b["generated"]} for r,b in
                      zip(protected,before[len(holdout):]) if b["generated"].strip()]
    conversation=[dialogue_for(r["user"],r["assistant"]) for r in train+protected_replay]
    examples=make_aligned_examples([("conversation",x) for x in conversation],
                                   tok,model.context_length,assistant_only=True)
    x,y,m=examples.tensors
    if int(m.sum())<=0:raise ValueError("no target tokens")
    args.output_dir.mkdir(parents=True,exist_ok=False)
    opt=torch.optim.AdamW(model.parameters(),lr=args.lr,weight_decay=0.01)
    losses=[]
    for step in range(args.steps):
        model.train();opt.zero_grad(set_to_none=True)
        for i in range(len(x)):
            loss=masked_ce(model,x[i:i+1].to(device),y[i:i+1].to(device),m[i:i+1].to(device))
            (loss/len(x)).backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
        opt.step();losses.append(float(loss.detach().cpu()))
        if (step+1)%10==0:print(json.dumps({"step":step+1,"loss_last_example":losses[-1]}))
    after=evaluate(model,tok,holdout+protected,args.max_new_tokens)
    baseline_protected=before[len(holdout):]
    candidate_protected=after[len(holdout):]
    regressions=[p["id"] for p,q in zip(baseline_protected,candidate_protected)
                 if p["generated"]!=q["generated"]]
    candidate=args.output_dir/"daily-sft-candidate.pt"
    model.save_checkpoint(str(candidate),epoch=1,loss=losses[-1],
        metadata={"experiment":"DAILY_GENERATION_SFT_V0135847","approved_for_production":False})
    report.update({"status":"EXPERIMENTAL_CANDIDATE_UNVERIFIED",
                   "training_performed":True,"steps_completed":len(losses),
                   "candidate_checkpoint":str(candidate),"candidate_sha256":checksum(candidate),
                   "protected_changed_ids":regressions,"holdout_before":before[:len(holdout)],
                   "holdout_after":after[:len(holdout)],"protected_before":baseline_protected,
                   "protected_after":candidate_protected,
                   "holdout_exact_before":sum(x["generated"].strip()==x["reference"].strip() for x in before[:len(holdout)]),
                   "holdout_exact_after":sum(x["generated"].strip()==x["reference"].strip() for x in after[:len(holdout)])})
    (args.output_dir/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("status","candidate_checkpoint","protected_changed_ids",
        "holdout_exact_before","holdout_exact_after")},ensure_ascii=False))
    return report
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_experiment_v0135847.jsonl"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output-dir",type=Path,default=Path("results/daily_generation_v0135847"))
    p.add_argument("--steps",type=int,default=30)
    p.add_argument("--lr",type=float,default=2e-6)
    p.add_argument("--seed",type=int,default=135847)
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--run",action="store_true")
    p.add_argument("--acknowledge-experiment",action="store_true")
    run(p.parse_args())
if __name__=="__main__":main()
