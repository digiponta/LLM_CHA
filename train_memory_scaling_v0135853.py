"""v0.13.58.53: controlled 8/16/32/56 SFT scaling experiment.
Uses v0.13.58.52 implementation; extends its selection and adds heldout
generation/unchanged-protected probes to the final report. No promotion.
"""
import argparse,json
from pathlib import Path
from train_token_equivalence_v0135852 import run as run_fit,rows,predict,sha
from train_daily_generation_v0135847 import dataset

def validate(source,count):
    train,holdout,protected=dataset(source)
    if count not in (8,16,32,56) or len(train)<count:
        raise ValueError("bad count or insufficient train rows")
    if set(r["user"] for r in train)&set(r["user"] for r in holdout+protected):
        raise ValueError("evaluation leakage")
    return train,holdout,protected

def run(args):
    train,holdout,protected=validate(args.source,args.count)
    # Underlying v0.13.58.52 implementation handles 1,4,8; for scaling we
    # need the requested count validated and selected from the complete dataset.
    from train_token_equivalence_v0135852 import rows as all_rows
    from dialogue_format_v0135817 import dialogue_for
    from aligned_replay_examples_v0135816 import make_aligned_examples
    from train_japanese_foundation_v01344 import masked_ce
    import torch,random
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    if args.output.exists():raise FileExistsError(args.output)
    if not (1<=args.max_steps<=500 and 1<=args.check_every<=args.max_steps):raise ValueError("bounds")
    if not 0<args.lr<=1e-4:raise ValueError("lr")
    if not args.run:
        out={"status":"DRY_RUN","count":args.count,"train_available":len(train),
             "holdout":len(holdout),"protected":len(protected),
             "base_sha256":sha(args.base),"source_sha256":sha(args.source)}
        print(json.dumps(out,ensure_ascii=False,indent=2));return out
    if not args.acknowledge_experiment:raise ValueError("acknowledgement required")
    random.seed(args.seed);torch.manual_seed(args.seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(args.seed)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(str(args.tokenizer))
    model,_=LanguageModel.load_checkpoint(str(args.base),device=device)
    if model.vocab_size!=tok.vocab_size:raise ValueError("tokenizer mismatch")
    chosen=train[:args.count]
    samples=make_aligned_examples([("conversation",dialogue_for(r["user"],r["assistant"])) for r in chosen],
                                  tok,model.context_length,assistant_only=True)
    x,y,m=samples.tensors
    opt=torch.optim.AdamW(model.parameters(),lr=args.lr,weight_decay=0.01)
    def assess(step):
        model.eval()
        with torch.inference_mode():
            fit=[predict(model,tok,r,args.max_new_tokens) for r in chosen]
            held=[predict(model,tok,r,args.max_new_tokens) for r in holdout]
            guard=[predict(model,tok,r,args.max_new_tokens) for r in protected]
        return {"step":step,"fit_token_exact":sum(z["token_exact_body"] for z in fit),
                "fit_raw_exact":sum(z["raw_exact"] for z in fit),
                "holdout_token_exact":sum(z["token_exact_body"] for z in held),
                "holdout_raw_exact":sum(z["raw_exact"] for z in held),
                "fit":fit,"holdout":held,"protected":guard}
    events=[assess(0)];steps=0
    original_protected=events[0]["protected"]
    args.output.mkdir(parents=True,exist_ok=False)
    while steps<args.max_steps:
        for _ in range(min(args.check_every,args.max_steps-steps)):
            model.train();opt.zero_grad(set_to_none=True)
            for i in range(len(x)):
                loss=masked_ce(model,x[i:i+1].to(device),y[i:i+1].to(device),m[i:i+1].to(device))
                (loss/len(x)).backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
            opt.step();steps+=1
        current=assess(steps);events.append(current)
        changes=[r["id"] for r,old in zip(current["protected"],original_protected)
                 if r["generated_ids"]!=old["generated_ids"]]
        print(json.dumps({"step":steps,"fit_token_exact":current["fit_token_exact"],
                          "holdout_token_exact":current["holdout_token_exact"],
                          "protected_changed":changes},ensure_ascii=False))
        if current["fit_token_exact"]==len(chosen):break
    final=events[-1]
    regress=[r["id"] for r,old in zip(final["protected"],original_protected)
             if r["generated_ids"]!=old["generated_ids"]]
    ckpt=args.output/"scaling-candidate.pt"
    model.save_checkpoint(str(ckpt),epoch=1,metadata={
        "experiment":"MEMORY_SCALING_V0135853","production_approved":False})
    report={"version":"v0.13.58.53","status":"ALL_FIT_TOKEN_EXACT" if final["fit_token_exact"]==len(chosen) else "MAX_STEPS",
            "count":args.count,"steps":steps,"lr":args.lr,"base_sha256":sha(args.base),
            "source_sha256":sha(args.source),"checkpoint":str(ckpt),"checkpoint_sha256":sha(ckpt),
            "protected_changed_ids":regress,"holdout_independent":False,
            "production_approved":False,"events":events}
    (args.output/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_corrected_v0135849.jsonl"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--count",type=int,choices=(8,16,32,56),default=8)
    p.add_argument("--output",type=Path,default=Path("results/memory_scaling_v0135853_n8"))
    p.add_argument("--max-steps",type=int,default=150)
    p.add_argument("--check-every",type=int,default=10)
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--lr",type=float,default=2e-5)
    p.add_argument("--seed",type=int,default=135853)
    p.add_argument("--run",action="store_true")
    p.add_argument("--acknowledge-experiment",action="store_true")
    result=run(p.parse_args())
    print(json.dumps({k:result[k] for k in ("status","count")},ensure_ascii=False))
if __name__=="__main__":main()
