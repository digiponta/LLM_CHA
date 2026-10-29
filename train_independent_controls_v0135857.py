"""v0.13.58.57: independently control training pool size, supervised token
exposures, and optimizer updates. Exact budget uses partial loss masks.

Causal attention still reads full input windows; "token budget" counts only
supervised next-token targets, not all input/FLOP tokens. Sampling with
replacement is intentional and recorded. Experiment only, no promotion.
"""
import argparse,hashlib,json,random,time
from pathlib import Path
from dialogue_format_v0135817 import dialogue_for
from aligned_replay_examples_v0135816 import make_aligned_examples
from train_daily_generation_v0135847 import dataset
from train_japanese_foundation_v01344 import masked_ce
from train_token_equivalence_v0135852 import predict

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def allocation(budget,updates):
    if updates<1 or budget<updates:raise ValueError("Require budget >= updates >= 1")
    q,r=divmod(budget,updates)
    return [q+(i<r) for i in range(updates)]
def choose_masks(mask,amount,start):
    """Build one deterministic rotating pass over supervised positions.
    Repeated passes are allowed when amount exceeds pool size.
    Returns [(sample_index, position_indices)] and next cursor.
    """
    import torch
    pos=torch.nonzero(mask>0,as_tuple=False).tolist()
    if not pos:raise ValueError("no supervised positions")
    indices=[pos[(start+j)%len(pos)] for j in range(amount)]
    grouped={}
    for sample,token in indices:grouped.setdefault(sample,[]).append(token)
    return grouped,(start+amount)%len(pos)
def quality(items):
    return {"token_exact":sum(i["token_exact_body"] for i in items),
            "raw_exact":sum(i["raw_exact"] for i in items),
            "nfkc_exact":sum(i["nfkc_equal"] for i in items),"total":len(items)}
def run(a):
    if a.output.exists():raise FileExistsError(a.output)
    if a.count not in (8,16,32,56):raise ValueError("count must be 8,16,32,56")
    if a.updates>500 or a.token_budget>500000 or not (0<a.lr<=1e-4):raise ValueError("bounds")
    budgets=allocation(a.token_budget,a.updates)
    train,holdout,protected=dataset(a.source)
    if len(train)<a.count:raise ValueError("insufficient training rows")
    chosen=train[:a.count]
    prompts=[set(r["user"] for r in part) for part in (chosen,holdout,protected)]
    if any(prompts[i]&prompts[j] for i,j in ((0,1),(0,2),(1,2))):raise ValueError("split overlap")
    meta={"version":"v0.13.58.57","count":a.count,"token_budget":a.token_budget,
          "updates_requested":a.updates,"lr":a.lr,"source_sha256":sha(a.source),
          "base_sha256":sha(a.base),"tokenizer_sha256":sha(a.tokenizer),
          "supervision_definition":"sum of masked next-token targets including EOS",
          "sampling":"rotating supervised positions, with replacement when exhausted",
          "production_approved":False,"holdout_independent":False}
    if not a.run:
        print(json.dumps({**meta,"status":"DRY_RUN","allocation":budgets},ensure_ascii=False,indent=2));return
    if not a.acknowledge_experiment:raise ValueError("acknowledgement required")
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    random.seed(a.seed);torch.manual_seed(a.seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(a.seed)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(str(a.tokenizer))
    model,_=LanguageModel.load_checkpoint(str(a.base),device=device)
    if model.vocab_size!=tok.vocab_size:raise ValueError("tokenizer mismatch")
    def tensors(rows):
        return make_aligned_examples([("conversation",dialogue_for(r["user"],r["assistant"])) for r in rows],
             tok,model.context_length,assistant_only=True).tensors
    fx,fy,fm=tensors(chosen)
    vx,vy,vm=tensors(holdout)
    opt=torch.optim.AdamW(model.parameters(),lr=a.lr,weight_decay=0.01)
    def validation_nll():
        model.eval();weighted=0.;n=0
        with torch.inference_mode():
            for i in range(len(vx)):
                w=int(vm[i].sum().item())
                loss=masked_ce(model,vx[i:i+1].to(device),vy[i:i+1].to(device),vm[i:i+1].to(device))
                weighted+=float(loss.item())*w;n+=w
        return weighted/n
    initial_protected=None
    exposures=0;cursor=0;t0=time.perf_counter()
    a.output.mkdir(parents=True,exist_ok=False)
    events=[]
    def snapshot(step):
        nonlocal initial_protected
        model.eval()
        with torch.inference_mode():
            fit=[predict(model,tok,r,a.max_new_tokens) for r in chosen]
            hold=[predict(model,tok,r,a.max_new_tokens) for r in holdout]
            prot=[predict(model,tok,r,a.max_new_tokens) for r in protected]
        if initial_protected is None:initial_protected={r["id"]:r["generated_ids"] for r in prot}
        changed=[r["id"] for r in prot if r["generated_ids"]!=initial_protected[r["id"]]]
        rec={"updates":step,"supervised_token_exposures":exposures,
             "validation_nll":validation_nll(),"fit":quality(fit),"holdout":quality(hold),
             "protected_changed_ids":changed,"elapsed_seconds":round(time.perf_counter()-t0,3),
             "holdout_generations":hold}
        events.append(rec)
        with (a.output/"metrics.jsonl").open("a",encoding="utf-8") as f:f.write(json.dumps(rec,ensure_ascii=False)+"\n")
        print(json.dumps({k:rec[k] for k in ("updates","supervised_token_exposures","validation_nll","fit","holdout","protected_changed_ids")},ensure_ascii=False),flush=True)
    snapshot(0)
    for step,b in enumerate(budgets,1):
        grouped,cursor=choose_masks(fm,b,cursor)
        model.train();opt.zero_grad(set_to_none=True)
        # Each target occurrence contributes equally even with partial final masks.
        # Multiple occurrences of the same position count repeatedly.
        for index,positions in grouped.items():
            extra=torch.zeros_like(fm[index:index+1])
            for pos in positions:extra[0,pos]+=1.
            # masked_ce normalizes by sum(mask); weight loss back by that count.
            weights=float(extra.sum().item())
            loss=masked_ce(model,fx[index:index+1].to(device),
                fy[index:index+1].to(device),extra.to(device))
            (loss*(weights/b)).backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);opt.step()
        exposures+=b
        if step%a.check_every==0 or step==a.updates:snapshot(step)
    if exposures!=a.token_budget:raise AssertionError("budget mismatch")
    report={**meta,"status":"EXPERIMENT_COMPLETE_NOT_APPROVED",
            "actual_updates":a.updates,"actual_supervised_token_exposures":exposures,
            "train_pool_supervised_tokens":int(fm.sum().item()),
            "validation_supervised_tokens":int(vm.sum().item()),
            "final":events[-1],"metrics_file":str(a.output/"metrics.jsonl")}
    (a.output/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_corrected_v0135849.jsonl"))
    p.add_argument("--base",type=Path,default=Path("model/model-gpu-v1.6.2-online.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--count",type=int,choices=(8,16,32,56),required=True)
    p.add_argument("--token-budget",type=int,required=True)
    p.add_argument("--updates",type=int,required=True)
    p.add_argument("--check-every",type=int,default=5)
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--lr",type=float,default=2e-5)
    p.add_argument("--seed",type=int,default=135857)
    p.add_argument("--run",action="store_true")
    p.add_argument("--acknowledge-experiment",action="store_true")
    run(p.parse_args())
if __name__=="__main__":main()
