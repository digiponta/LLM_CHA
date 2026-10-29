"""v0.13.58.58 exact TRAIN supervised-token budget + separate protected replay.
No production promotion. Training tokens / updates independently controlled.
Replay budget is additional and is explicitly reported; holdout has no gradients.
"""
import argparse,hashlib,json,random,time
from pathlib import Path
from dialogue_format_v0135817 import dialogue_for
from aligned_replay_examples_v0135816 import make_aligned_examples
from train_daily_generation_v0135847 import dataset
from train_japanese_foundation_v01344 import masked_ce
from train_token_equivalence_v0135852 import predict
from train_independent_controls_v0135857 import allocation,choose_masks,quality

def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replay_allocation(train_budget,ratio):
    if ratio not in (0,0.25,0.5):raise ValueError("invalid replay ratio")
    if ratio==0:return 0
    # replay / (train + replay) = ratio, so total loss weights are naturally balanced.
    return round(train_budget*ratio/(1-ratio))
def run(a):
    if a.output.exists():raise FileExistsError(a.output)
    if not 1<=a.updates<=300 or not 1<=a.check_every<=a.updates or not 0<a.lr<=1e-4:raise ValueError("bounds")
    train_budgets=allocation(a.train_token_budget,a.updates)
    replay_total=replay_allocation(a.train_token_budget,a.replay_ratio)
    replay_budgets=([0]*a.updates if not replay_total else
                    [int(replay_total*(i+1)/a.updates)-int(replay_total*i/a.updates) for i in range(a.updates)])
    train,holdout,protected=dataset(a.source)
    if len(train)!=56 or len(protected)<2:raise ValueError("requires 56 training and 2 protected records")
    data={"version":"v0.13.58.58","train_count":56,"train_token_budget":a.train_token_budget,
          "replay_token_budget":replay_total,"updates":a.updates,"replay_ratio":a.replay_ratio,
          "source_sha256":hashfile(a.source),"base_sha256":hashfile(a.base),
          "tokenizer_sha256":hashfile(a.tokenizer),"holdout_independent":False,
          "production_approved":False}
    if not a.run:
        print(json.dumps({**data,"status":"DRY_RUN"},ensure_ascii=False));return data
    if not a.acknowledge_experiment:raise ValueError("acknowledgement required")
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    random.seed(a.seed);torch.manual_seed(a.seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(a.seed)
    dev=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(str(a.tokenizer))
    model,_=LanguageModel.load_checkpoint(str(a.base),device=dev)
    if model.vocab_size!=tok.vocab_size:raise ValueError("vocab mismatch")
    def pack(rows):
        return make_aligned_examples([("conversation",dialogue_for(r["user"],r["assistant"])) for r in rows],
                tok,model.context_length,assistant_only=True).tensors
    train_pack=pack(train);hold_pack=pack(holdout)
    model.eval()
    with torch.inference_mode(): baseline=[predict(model,tok,r,a.max_new_tokens) for r in protected]
    originals={r["id"]:r["generated_ids"] for r in baseline}
    replay=[{"user":r["user"],"assistant":b["generated"]} for r,b in zip(protected,baseline)
            if b["generated"].strip() and "\ufffd" not in b["generated"]]
    if replay_total and len(replay)!=len(protected):raise ValueError("cannot construct complete protected replay")
    replay_pack=pack(replay) if replay_total else None
    opt=torch.optim.AdamW(model.parameters(),lr=a.lr,weight_decay=0.01)
    a.output.mkdir(parents=True,exist_ok=False)
    events=[];tc=rc=0;train_exposure=replay_exposure=0;clock=time.perf_counter()
    def validation_nll():
        x,y,m=hold_pack;weighted=0.;tokens=0
        model.eval()
        with torch.inference_mode():
            for i in range(len(x)):
                cnt=int(m[i].sum().item())
                loss=masked_ce(model,x[i:i+1].to(dev),y[i:i+1].to(dev),m[i:i+1].to(dev))
                weighted+=float(loss.item())*cnt;tokens+=cnt
        return weighted/tokens
    def assess(step):
        model.eval()
        with torch.inference_mode():
            fit=[predict(model,tok,r,a.max_new_tokens) for r in train]
            held=[predict(model,tok,r,a.max_new_tokens) for r in holdout]
            guard=[predict(model,tok,r,a.max_new_tokens) for r in protected]
        changed=[r["id"] for r in guard if r["generated_ids"]!=originals[r["id"]]]
        e={"updates":step,"train_token_exposures":train_exposure,"replay_token_exposures":replay_exposure,
           "validation_nll":validation_nll(),"fit":quality(fit),"holdout":quality(held),
           "protected_changed_ids":changed,"elapsed_seconds":round(time.perf_counter()-clock,3),
           "holdout_generations":held}
        events.append(e)
        with (a.output/"metrics.jsonl").open("a",encoding="utf-8") as f:f.write(json.dumps(e,ensure_ascii=False)+"\n")
        print(json.dumps({k:e[k] for k in ("updates","train_token_exposures","replay_token_exposures","validation_nll","fit","holdout","protected_changed_ids")},ensure_ascii=False),flush=True)
    assess(0)
    def gradient_batch(pack,amount,cursor,weight):
        x,y,m=pack
        groups,cursor=choose_masks(m,amount,cursor)
        for index,positions in groups.items():
            mask=torch.zeros_like(m[index:index+1])
            for pos in positions:mask[0,pos]+=1
            cnt=float(mask.sum().item())
            loss=masked_ce(model,x[index:index+1].to(dev),y[index:index+1].to(dev),mask.to(dev))
            (loss*(cnt/amount)*weight).backward()
        return cursor
    for step,(t,r) in enumerate(zip(train_budgets,replay_budgets),1):
        model.train();opt.zero_grad(set_to_none=True)
        # Relative gradient weights set by actual train/replay counts *within this update*.
        total=t+r
        tc=gradient_batch(train_pack,t,tc,t/total)
        if r:rc=gradient_batch(replay_pack,r,rc,r/total)
        torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);opt.step()
        train_exposure+=t;replay_exposure+=r
        if step%a.check_every==0 or step==a.updates:assess(step)
    assert train_exposure==a.train_token_budget and replay_exposure==replay_total
    data.update({"status":"EXPERIMENT_COMPLETE_NOT_APPROVED","final":events[-1],
                 "actual_train_exposures":train_exposure,"actual_replay_exposures":replay_exposure,
                 "train_pool_supervised_tokens":int(train_pack[2].sum().item()),
                 "protected_probe_count":len(protected)})
    (a.output/"report.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return data
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_corrected_v0135849.jsonl"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--train-token-budget",type=int,required=True)
    p.add_argument("--updates",type=int,required=True)
    p.add_argument("--replay-ratio",type=float,required=True)
    p.add_argument("--check-every",type=int,default=5)
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--lr",type=float,default=2e-5)
    p.add_argument("--seed",type=int,default=135858)
    p.add_argument("--run",action="store_true")
    p.add_argument("--acknowledge-experiment",action="store_true")
    a=p.parse_args();run(a)
if __name__=="__main__":main()
