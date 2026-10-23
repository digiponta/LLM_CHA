"""v0.7.30 Experimental Adapter generation-length sweep (read only)."""
import argparse
import hashlib
import json
import time
from pathlib import Path

BUDGETS=(32,64,128,256)

def digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def common_prefix(a,b):
    n=0
    for x,y in zip(a,b):
        if x!=y:break
        n+=1
    return n

def sweep(rows,tokenizer,generate_fn,budgets=BUDGETS):
    if not rows:raise ValueError("No PENDING Nagato records")
    report=[]
    for budget in budgets:
        cases=[]
        for row in rows:
            target=tokenizer.encode(row["answer"])
            started=time.perf_counter()
            generated=generate_fn(row["question"],budget)
            seconds=time.perf_counter()-started
            tokens=tokenizer.encode(generated)
            prefix=common_prefix(tokens,target)
            cases.append({"candidate_id":row["id"],"source_id":row["source_id"],
                "answer_tokens":len(target),"generated_tokens":len(tokens),
                "budget_can_fit":len(target)<=budget,
                "exact_match":generated.strip()==row["answer"].strip(),
                "prefix_tokens":prefix,
                "prefix_ratio":prefix/len(target) if target else None,
                "elapsed_seconds":seconds,
                "generated_preview":generated[:200]})
        report.append({"max_new_tokens":budget,"count":len(cases),
            "exact":sum(c["exact_match"] for c in cases),
            "fit_count":sum(c["budget_can_fit"] for c in cases),
            "mean_prefix_ratio":sum(c["prefix_ratio"] or 0 for c in cases)/len(cases),
            "elapsed_seconds":sum(c["elapsed_seconds"] for c in cases),
            "cases":cases})
    return {"version":"v0.7.30","sweep":report,"auto_promote":False,
            "factual_verification":"NOT_PERFORMED"}

def run(args):
    import torch
    from dual_semantic_memory_v071 import DualMemory
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from dual_adapters_v073 import DualAdapterModel
    from evaluate_dual_adapter_v074 import load_experimental
    from dual_inference_v075 import generate
    protected=[Path(p).resolve() for p in
               (args.base,args.tokenizer,args.approved,args.candidates,args.adapter)
               if Path(p).exists()]
    destination=Path(args.output).resolve()
    if destination in protected:raise ValueError("output overlaps protected input")
    before={str(p):digest(p) for p in protected}
    records=[r for r in DualMemory(args.approved,args.candidates).candidates()
             if r["status"]=="PENDING" and r["source_id"].startswith("data-nagato.txt:")]
    if not records:raise ValueError("no PENDING Nagato records")
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base,_=LanguageModel.load_checkpoint(args.base,device=device)
    tok=Tokenizer.load(args.tokenizer)
    saved=torch.load(args.adapter,map_location="cpu",weights_only=True)
    if saved.get("route")!="experimental" or saved.get("approved") is not False:
        raise ValueError("invalid Experimental checkpoint")
    pending_ids={r["id"] for r in DualMemory(args.approved,args.candidates).candidates()
                 if r["status"]=="PENDING"}
    if set(saved.get("candidate_ids",[]))!=pending_ids:
        raise ValueError("checkpoint/PENDING snapshot mismatch")
    model=DualAdapterModel(base,rank=int(saved["rank"])).to(device)
    load_experimental(model,args.adapter)
    def inference(q,budget):
        return generate(model,tok,q,"experimental",budget)
    result=sweep(records,tok,inference)
    result["device"]=str(device)
    result["protected_before"]=before
    result["protected_after"]={str(p):digest(p) for p in protected}
    result["protected_unchanged"]=result["protected_before"]==result["protected_after"]
    if not result["protected_unchanged"]:raise RuntimeError("protected input changed")
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--approved",default="data/approved_v071.jsonl")
    p.add_argument("--candidates",default="data/candidates_v071.jsonl")
    p.add_argument("--adapter",required=True)
    p.add_argument("--output",default="results/nagato_sweep_v0730/report.json")
    args=p.parse_args()
    result=run(args)
    print(json.dumps({"version":result["version"],"device":result["device"],
        "protected_unchanged":result["protected_unchanged"],
        "sweep":[{k:x[k] for k in ("max_new_tokens","count","exact","fit_count","mean_prefix_ratio","elapsed_seconds")} for x in result["sweep"]]},
        ensure_ascii=False,indent=2))
    print("report:",args.output)
if __name__=="__main__":main()
