"""v0.7.41 read-only Trusted sleep verification (teacher-forced)."""
import argparse,hashlib,json
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def status_for_pairs(rows,state_fps,checkpoint_fps):
    records=[]
    for r in rows:
        fp=r["fingerprint"]
        records.append({"approved_id":r["id"],"fingerprint":fp,
                        "state_bound":fp in state_fps,"checkpoint_bound":fp in checkpoint_fps,
                        "both_bound":fp in state_fps and fp in checkpoint_fps})
    return records

def mean_nll(model,tokenizer,pairs,device):
    import torch
    import torch.nn.functional as F
    from online_train import ConversationDataset
    dataset=ConversationDataset(pairs,tokenizer,model.context_length)
    model.eval()
    results=[]
    with torch.no_grad():
        for (question,answer),(x,y,mask) in zip(pairs,dataset):
            x=x.unsqueeze(0).to(device);y=y.unsqueeze(0).to(device)
            pos=torch.where(mask>0)[0]
            if pos.numel()==0:raise ValueError("missing target tokens")
            logits=model(x)[0,pos]
            targets=y[0,pos]
            nll=float(-F.log_softmax(logits,dim=-1).gather(1,targets[:,None]).mean().item())
            first_logits=logits[0];first_target=int(targets[0])
            results.append({"question":question,"answer":answer,
                            "target_nll":nll,"target_tokens":int(pos.numel()),
                            "first_top1":int(first_logits.argmax())==first_target})
    return results

def summarize(items):
    if not items:return {"count":0,"mean_nll":None,"first_top1":0}
    return {"count":len(items),"mean_nll":sum(x["target_nll"] for x in items)/len(items),
            "first_top1":sum(x["first_top1"] for x in items)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--before",default=None,help="Original pre-sleep checkpoint, if retained")
    p.add_argument("--after",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--approved-ledger",default="data/approved_semantic_memory_v0740.jsonl")
    p.add_argument("--state",default="data/chat_learning_state.json")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--stability",default="data/stability_replay_v104.jsonl")
    p.add_argument("--output",default="results/trusted_retention_v0741.json")
    args=p.parse_args()
    from approved_semantic_sleep_v0740 import _load_jsonl
    from internalized_knowledge_v10100 import load_trained_fingerprints
    from online_train import checkpoint_trained_fingerprints,load_chat_jsonl
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    import torch
    ledger=_load_jsonl(args.approved_ledger)
    if not ledger:raise ValueError("no Approved ledger entries")
    protected=[Path(v).resolve() for v in (args.after,args.approved_ledger,args.state,args.tokenizer)]
    if args.before:protected.append(Path(args.before).resolve())
    if Path(args.stability).exists():protected.append(Path(args.stability).resolve())
    if Path(args.output).resolve() in protected:raise ValueError("output overlaps input")
    before_hash={str(x):sha(x) for x in protected}
    state=load_trained_fingerprints(Path(args.state))
    checkpoint=checkpoint_trained_fingerprints(Path(args.after))
    binding=status_for_pairs(ledger,state,checkpoint)
    if args.stability and Path(args.stability).exists():
        stability=[(u,a) for u,a,_ in load_chat_jsonl(Path(args.stability))]
    else:stability=[]
    approved_pairs=[(r["user"],r["assistant"]) for r in ledger]
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer=Tokenizer.load(args.tokenizer)
    measurements={}
    for key,path in (("before",args.before),("after",args.after)):
        if path is None:continue
        model,_=LanguageModel.load_checkpoint(path,device=device)
        approved_nll=mean_nll(model,tokenizer,approved_pairs,device)
        stable_nll=mean_nll(model,tokenizer,stability,device) if stability else []
        measurements[key]={"approved":summarize(approved_nll),
                           "stability":summarize(stable_nll),
                           "approved_cases":approved_nll,"stability_cases":stable_nll}
    comparison=None
    if "before" in measurements:
        a=measurements["before"];b=measurements["after"]
        comparison={"approved_nll_gain":a["approved"]["mean_nll"]-b["approved"]["mean_nll"],
                    "stability_nll_change":b["stability"]["mean_nll"]-a["stability"]["mean_nll"] if stability else None}
    if before_hash!={str(x):sha(x) for x in protected}:raise RuntimeError("protected input changed")
    result={"version":"v0.7.41","device":str(device),"approved_binding":binding,
            "checkpoint_bound_count":sum(r["both_bound"] for r in binding),
            "approved_total":len(binding),"measurements":measurements,
            "comparison":comparison,"protected_unchanged":True,
            "scope":"TEACHER_FORCED_ONLY","free_generation_verified":False,
            "note":"A pre-sleep checkpoint is needed for a true before/after comparison; binding is not proof of correct free generation."}
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("version","device","approved_total","checkpoint_bound_count","comparison","protected_unchanged")},ensure_ascii=False,indent=2))
    print("Report:",out)
if __name__=="__main__":main()
