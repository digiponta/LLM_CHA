"""v0.13.58.54: protected replay 0 / 25 / 50 percent sweep.
Ratios are fractions of gradient weight, not dataset cardinality. Never promote.
"""
import argparse,json,random,hashlib
from pathlib import Path
from train_daily_generation_v0135847 import dataset
from train_token_equivalence_v0135852 import predict
from dialogue_format_v0135817 import dialogue_for
from aligned_replay_examples_v0135816 import make_aligned_examples
from train_japanese_foundation_v01344 import masked_ce

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replay_weights(ratio):
    if ratio not in (0.0,0.25,0.5):raise ValueError("ratio must be 0, 0.25 or 0.5")
    return 1-ratio,ratio
def run(a):
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    if a.output.exists():raise FileExistsError(a.output)
    if a.steps<1 or a.steps>300 or a.check_every<1 or a.lr<=0 or a.lr>1e-4:raise ValueError("bounds")
    w_train,w_replay=replay_weights(a.replay_ratio)
    train,holdout,protected=dataset(a.source)
    if len(train)!=56 or len(protected)<2:raise ValueError("requires 56 train and protected probes")
    random.seed(a.seed);torch.manual_seed(a.seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(a.seed)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(str(a.tokenizer))
    model,_=LanguageModel.load_checkpoint(str(a.base),device=device)
    if model.vocab_size!=tok.vocab_size:raise ValueError("vocab mismatch")
    def probe(items):
        model.eval()
        with torch.inference_mode():return [predict(model,tok,r,a.max_new_tokens) for r in items]
    baseline=probe(protected)
    baseline_map={z["id"]:z["generated_ids"] for z in baseline}
    # Replay actual base output, rather than forcing potentially incorrect protected references.
    replay=[{"user":r["user"],"assistant":v["generated"]} for r,v in zip(protected,baseline)
            if v["generated"].strip() and "\ufffd" not in v["generated"]]
    if w_replay and not replay:raise ValueError("no valid protected replay outputs")
    fit=make_aligned_examples([("conversation",dialogue_for(r["user"],r["assistant"])) for r in train],tok,model.context_length,assistant_only=True)
    rx=make_aligned_examples([("conversation",dialogue_for(r["user"],r["assistant"])) for r in replay],tok,model.context_length,assistant_only=True) if replay else None
    fx,fy,fm=fit.tensors
    opt=torch.optim.AdamW(model.parameters(),lr=a.lr,weight_decay=0.01)
    a.output.mkdir(parents=True,exist_ok=False)
    events=[];first_safe=None;step=0
    for step in range(1,a.steps+1):
        model.train();opt.zero_grad(set_to_none=True)
        for i in range(len(fx)):
            loss=masked_ce(model,fx[i:i+1].to(device),fy[i:i+1].to(device),fm[i:i+1].to(device))
            (loss*w_train/len(fx)).backward()
        if w_replay:
            x,y,m=rx.tensors
            for i in range(len(x)):
                loss=masked_ce(model,x[i:i+1].to(device),y[i:i+1].to(device),m[i:i+1].to(device))
                (loss*w_replay/len(x)).backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);opt.step()
        if step%a.check_every and step!=a.steps:continue
        trained=probe(train);held=probe(holdout);guard=probe(protected)
        changed=[z["id"] for z in guard if z["generated_ids"]!=baseline_map[z["id"]]]
        e={"step":step,"fit_token_exact":sum(z["token_exact_body"] for z in trained),
           "holdout_token_exact":sum(z["token_exact_body"] for z in held),
           "protected_changed_ids":changed,"protected_results":guard,
           "holdout_results":held}
        events.append(e)
        print(json.dumps({k:e[k] for k in ("step","fit_token_exact","holdout_token_exact","protected_changed_ids")},ensure_ascii=False))
        if not changed and e["fit_token_exact"]>0:
            checkpoint=a.output/f"safe-step-{step}.pt"
            model.save_checkpoint(str(checkpoint),epoch=1,metadata={"experiment":"PROTECTED_REPLAY_V0135854","production_approved":False})
            first_safe=str(checkpoint)
        if e["fit_token_exact"]==len(train) and not changed:break
    final=events[-1]
    report={"version":"v0.13.58.54","status":"FIT_AND_PROTECTED_PASS" if final["fit_token_exact"]==len(train) and not final["protected_changed_ids"] else "NOT_ACCEPTED",
        "replay_ratio":a.replay_ratio,"steps":step,"base_sha256":sha(a.base),"source_sha256":sha(a.source),
        "last_safe_checkpoint":first_safe,"events":events,"holdout_independent":False,
        "production_approved":False,"protected_probes":len(protected)}
    (a.output/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"last_safe_checkpoint":first_safe},ensure_ascii=False))
    return report
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_corrected_v0135849.jsonl"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--replay-ratio",type=float,required=True)
    p.add_argument("--steps",type=int,default=100)
    p.add_argument("--check-every",type=int,default=10)
    p.add_argument("--lr",type=float,default=2e-5)
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--seed",type=int,default=135854)
    p.add_argument("--run",action="store_true")
    p.add_argument("--acknowledge-experiment",action="store_true")
    a=p.parse_args()
    if not a.run or not a.acknowledge_experiment:raise ValueError("explicit --run --acknowledge-experiment required")
    run(a)
if __name__=="__main__":main()
