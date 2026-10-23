"""v0.7.31 Target NLL and first-answer-token ranking; read-only."""
import argparse,hashlib,json,math
from pathlib import Path
import torch
import torch.nn.functional as F

def file_hash(path):
    if not Path(path).exists(): return None
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1048576),b""):h.update(block)
    return h.hexdigest()

@torch.no_grad()
def diagnose(model,tokenizer,pairs,device,top_k=5):
    from online_train import ConversationDataset
    dataset=ConversationDataset([(r["question"],r["answer"]) for r in pairs],
                                tokenizer,model.base.context_length)
    results=[]
    model.eval()
    for record,(x,y,mask) in zip(pairs,dataset):
        x=x.unsqueeze(0).to(device);y=y.unsqueeze(0).to(device)
        mask=mask.unsqueeze(0).to(device)
        positions=torch.where(mask[0]>0)[0]
        if not len(positions):raise ValueError("empty answer supervision")
        first=int(positions[0])
        variants={}
        for route in ("base","experimental"):
            logits=model.base(x) if route=="base" else model(x,route=route)
            selected=logits[0,positions]
            targets=y[0,positions]
            logprob=F.log_softmax(selected,dim=-1)
            nll=float(-logprob.gather(1,targets[:,None]).mean().item())
            first_logits=logits[0,first]
            target=int(y[0,first])
            rank=int((first_logits>first_logits[target]).sum().item())+1
            predictions=first_logits.topk(min(top_k,first_logits.numel())).indices.tolist()
            variants[route]={"target_nll":nll,"first_rank":rank,
                "first_top1":rank==1,"first_topk":rank<=top_k,
                "target_first_token":target,"predicted_token_ids":predictions}
        results.append({"candidate_id":record["id"],"source_id":record["source_id"],
            "question":record["question"],"answer_chars":len(record["answer"]),
            "supervised_tokens":len(positions),
            "base":variants["base"],"experimental":variants["experimental"],
            "nll_gain":variants["base"]["target_nll"]-variants["experimental"]["target_nll"]})
    return {"count":len(results),"base_mean_nll":sum(x["base"]["target_nll"] for x in results)/len(results),
        "experimental_mean_nll":sum(x["experimental"]["target_nll"] for x in results)/len(results),
        "first_top1_base":sum(x["base"]["first_top1"] for x in results),
        "first_top1_experimental":sum(x["experimental"]["first_top1"] for x in results),
        "first_topk_base":sum(x["base"]["first_topk"] for x in results),
        "first_topk_experimental":sum(x["experimental"]["first_topk"] for x in results),
        "cases":results}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--approved",default="data/approved_v071.jsonl")
    p.add_argument("--candidates",default="data/candidates_v071.jsonl")
    p.add_argument("--adapter",required=True)
    p.add_argument("--top-k",type=int,default=5)
    p.add_argument("--output",default="results/nagato_nll_v0731/report.json")
    args=p.parse_args()
    if args.top_k<1:raise ValueError("--top-k must be positive")
    from dual_semantic_memory_v071 import DualMemory
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from dual_adapters_v073 import DualAdapterModel
    from evaluate_dual_adapter_v074 import load_experimental
    paths=[Path(t).resolve() for t in (args.base,args.tokenizer,args.candidates,args.adapter)]
    if Path(args.approved).exists():paths.append(Path(args.approved).resolve())
    if Path(args.output).resolve() in paths:raise ValueError("output overlaps inputs")
    before={str(path):file_hash(path) for path in paths}
    mem=DualMemory(args.approved,args.candidates)
    pending=[r for r in mem.candidates() if r["status"]=="PENDING"]
    if not pending:raise ValueError("no pending records")
    saved=torch.load(args.adapter,map_location="cpu",weights_only=True)
    if saved.get("route")!="experimental" or saved.get("approved") is not False:raise ValueError("invalid experimental adapter")
    if set(saved.get("candidate_ids",[]))!={r["id"] for r in pending}:
        raise ValueError("checkpoint does not match PENDING records")
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    base,_=LanguageModel.load_checkpoint(args.base,device=device)
    tokenizer=Tokenizer.load(args.tokenizer)
    model=DualAdapterModel(base,rank=int(saved["rank"])).to(device)
    load_experimental(model,args.adapter)
    results=diagnose(model,tokenizer,pending,device,args.top_k)
    after={str(path):file_hash(path) for path in paths}
    if before!=after:raise RuntimeError("protected input changed")
    report={"version":"v0.7.31","device":str(device),"top_k":args.top_k,
       "protected_unchanged":True,"auto_promote":False,
       "training_probe_only":True,"factual_verification":"NOT_PERFORMED",**results}
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("version","device","count","base_mean_nll",
      "experimental_mean_nll","first_top1_base","first_top1_experimental",
      "first_topk_base","first_topk_experimental","protected_unchanged")},ensure_ascii=False,indent=2))
    print("report:",out)
if __name__=="__main__":main()
