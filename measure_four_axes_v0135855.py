"""v0.13.58.55 four-axis measurement: token exposures, updates, validation NLL,
and free-running generation. Experimental only. Holdout never used for gradients.
"""
import argparse,hashlib,json,random,time
from pathlib import Path
from dialogue_format_v0135817 import dialogue_for
from aligned_replay_examples_v0135816 import make_aligned_examples
from train_japanese_foundation_v01344 import masked_ce
from train_daily_generation_v0135847 import dataset
from train_token_equivalence_v0135852 import predict

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def exact_stats(results):
    return {"exact":sum(x["token_exact_body"] for x in results),
            "raw_exact":sum(x["raw_exact"] for x in results),
            "nfkc_exact":sum(x["nfkc_equal"] for x in results),"total":len(results)}
def validate_split(train,holdout,protected):
    questions=[set(x["user"] for x in part) for part in (train,holdout,protected)]
    if any(questions[i]&questions[j] for i,j in ((0,1),(0,2),(1,2))):
        raise ValueError("overlapping questions between splits")
def build(tok,context,records):
    ex=make_aligned_examples([("conversation",dialogue_for(r["user"],r["assistant"])) for r in records],
                             tok,context,assistant_only=True)
    return ex.tensors
def nll(model,triplet,device):
    import torch
    x,y,m=triplet
    total=0.;count=0
    model.eval()
    with torch.inference_mode():
        for i in range(len(x)):
            weight=float(m[i].sum())
            if not weight:continue
            loss=masked_ce(model,x[i:i+1].to(device),y[i:i+1].to(device),m[i:i+1].to(device))
            total+=float(loss.item())*weight;count+=int(weight)
    return total/count if count else None
def run(a):
    if a.output.exists():raise FileExistsError(a.output)
    if a.train_count not in (8,16,32,56) or not 1<=a.steps<=300 or not 1<=a.check_every<=a.steps:raise ValueError("invalid bounds")
    if not 0<a.lr<=1e-4 or not 0<=a.replay_ratio<=0.5:raise ValueError("invalid lr/ratio")
    train,holdout,protected=dataset(a.source)
    validate_split(train,holdout,protected)
    if len(train)<a.train_count:raise ValueError("insufficient train rows")
    subset=train[:a.train_count]
    stub={"version":"v0.13.58.55","train_count":a.train_count,
          "base_sha256":digest(a.base),"source_sha256":digest(a.source),
          "tokenizer_sha256":digest(a.tokenizer),"holdout_independent":False,
          "production_approved":False}
    if not a.run:
        print(json.dumps({**stub,"status":"DRY_RUN"},ensure_ascii=False,indent=2));return
    if not a.acknowledge_experiment:raise ValueError("acknowledgement required")
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    random.seed(a.seed);torch.manual_seed(a.seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(a.seed)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(str(a.tokenizer))
    model,_=LanguageModel.load_checkpoint(str(a.base),device=device)
    if model.vocab_size!=tok.vocab_size:raise ValueError("vocab mismatch")
    fit=build(tok,model.context_length,subset)
    valid=build(tok,model.context_length,holdout)
    baseline_protected=[predict(model,tok,r,a.max_new_tokens) for r in protected]
    baseline_ids={r["id"]:r["generated_ids"] for r in baseline_protected}
    replay=[{"user":r["user"],"assistant":generated["generated"]} for r,generated in zip(protected,baseline_protected)
            if generated["generated"].strip() and "\ufffd" not in generated["generated"]]
    if a.replay_ratio and not replay:raise ValueError("no valid replay targets")
    replay_data=build(tok,model.context_length,replay) if replay else None
    train_tokens=int(fit[2].sum().item())
    replay_tokens=int(replay_data[2].sum().item()) if replay_data else 0
    validation_tokens=int(valid[2].sum().item())
    opt=torch.optim.AdamW(model.parameters(),lr=a.lr,weight_decay=0.01)
    a.output.mkdir(parents=True,exist_ok=False)
    metrics_path=a.output/"metrics.jsonl"
    history=[]
    t0=time.perf_counter()
    def evaluate(step):
        model.eval()
        with torch.inference_mode():
            gen_holdout=[predict(model,tok,r,a.max_new_tokens) for r in holdout]
            gen_protected=[predict(model,tok,r,a.max_new_tokens) for r in protected]
            # Train fit is measured to separate memorization from generalization.
            gen_train=[predict(model,tok,r,a.max_new_tokens) for r in subset]
        changed=[r["id"] for r in gen_protected if r["generated_ids"]!=baseline_ids[r["id"]]]
        values={"step":step,"updates":step,
                "supervised_token_exposures":step*(train_tokens+replay_tokens),
                "train_token_exposures":step*train_tokens,
                "replay_token_exposures":step*replay_tokens,
                "all_input_tokens_per_step":int(fit[0].numel())+(int(replay_data[0].numel()) if replay_data else 0),
                "elapsed_seconds":round(time.perf_counter()-t0,3),
                "train_nll":nll(model,fit,device),"validation_nll":nll(model,valid,device),
                "fit":exact_stats(gen_train),"holdout":exact_stats(gen_holdout),
                "protected_changed_ids":changed,"holdout_generations":gen_holdout,
                "protected_generations":gen_protected}
        history.append(values)
        with metrics_path.open("a",encoding="utf-8") as f:f.write(json.dumps(values,ensure_ascii=False)+"\n")
        print(json.dumps({k:values[k] for k in ("step","train_token_exposures","replay_token_exposures","validation_nll","fit","holdout","protected_changed_ids")},ensure_ascii=False),flush=True)
        return values
    evaluate(0)
    fx,fy,fm=fit
    for step in range(1,a.steps+1):
        model.train();opt.zero_grad(set_to_none=True)
        for i in range(len(fx)):
            loss=masked_ce(model,fx[i:i+1].to(device),fy[i:i+1].to(device),fm[i:i+1].to(device))
            (loss*(1-a.replay_ratio)/len(fx)).backward()
        if a.replay_ratio:
            rx,ry,rm=replay_data
            for i in range(len(rx)):
                loss=masked_ce(model,rx[i:i+1].to(device),ry[i:i+1].to(device),rm[i:i+1].to(device))
                (loss*a.replay_ratio/len(rx)).backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
        opt.step()
        if step%a.check_every==0 or step==a.steps:
            evaluate(step)
    final=history[-1]
    report={**stub,"status":"EXPERIMENT_COMPLETE_NOT_APPROVED","steps":a.steps,"lr":a.lr,
            "replay_ratio":a.replay_ratio,"train_supervised_tokens_per_step":train_tokens,
            "replay_supervised_tokens_per_step":replay_tokens,"validation_supervised_tokens":validation_tokens,
            "metrics_file":str(metrics_path),"final_metrics":final,
            "warning":"Exact generation rate is not semantic quality. Holdout is exploratory, not independent."}
    (a.output/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_corrected_v0135849.jsonl"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--train-count",type=int,choices=(8,16,32,56),default=56)
    p.add_argument("--steps",type=int,default=60)
    p.add_argument("--check-every",type=int,default=10)
    p.add_argument("--lr",type=float,default=2e-5)
    p.add_argument("--replay-ratio",type=float,default=0.25)
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--seed",type=int,default=135855)
    p.add_argument("--run",action="store_true")
    p.add_argument("--acknowledge-experiment",action="store_true")
    run(p.parse_args())
if __name__=="__main__":main()
