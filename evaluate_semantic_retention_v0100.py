"""Read-only, model-only Nagato Semantic Memory retention benchmark.

Measures teacher-forced answer NLL, not QA accuracy. Never invokes chat.py,
retrieval, prompts from Semantic Memory at inference, or training.
"""
import argparse
import json
from pathlib import Path

def answer_nll(model, tokenizer, question, answer, device):
    import torch
    import torch.nn.functional as F
    prefix=tokenizer.encode("ユーザー: "+question+"\nAI: ",add_bos=True)
    target=tokenizer.encode(answer,add_eos=True)
    if not prefix or not target:
        return None
    ids=(prefix+target)[-model.context_length:]
    # Evaluate only answer targets that fit in the available context.
    retained_target=min(len(target),len(ids)-1)
    if retained_target<=0:
        return None
    x=torch.tensor([ids[:-1]],device=device,dtype=torch.long)
    with torch.inference_mode():
        logits=model(x)[0]
        gold=torch.tensor(ids[1:],device=device,dtype=torch.long)
        per_token=F.cross_entropy(logits,gold,reduction="none")
    return float(per_token[-retained_target:].mean().item())

def summarize(values):
    good=[v for v in values if v is not None]
    return {"evaluated":len(good),"mean_answer_nll":sum(good)/len(good) if good else None}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--memory",default="data/nagato_semantic_memory_v10131.jsonl")
    p.add_argument("--tokenizer",default="../LLM_GPU/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--base",default="model/model-llm-try-nagato-chat-v94.pt")
    p.add_argument("--online",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--limit",type=int,default=56)
    p.add_argument("--output",default="results/semantic_retention_v0100.json")
    p.add_argument("--device",choices=["auto","cpu","cuda"],default="auto")
    args=p.parse_args()
    if args.limit<1: p.error("--limit must be positive")
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from semantic_sleep_learning_v10131 import load_nagato_semantic_memory
    device=torch.device("cuda" if args.device=="auto" and torch.cuda.is_available() else ("cpu" if args.device=="auto" else args.device))
    tok=Tokenizer.load(str(Path(args.tokenizer)))
    rows=load_nagato_semantic_memory(Path(args.memory))[:args.limit]
    models={}
    for name,path in (("base",args.base),("online",args.online)):
        m,_=LanguageModel.load_checkpoint(str(path),device=device)
        if m.vocab_size!=tok.vocab_size:raise ValueError("Tokenizer mismatch: "+name)
        m.eval();models[name]=m
    records=[]
    for r in rows:
        q=str(r.get("question",""));a=str(r.get("assistant",""))
        if not q or not a:continue
        values={name:answer_nll(model,tok,q,a,device) for name,model in models.items()}
        records.append({"concept":r.get("concept"),**values})
    base=summarize([r["base"] for r in records])
    online=summarize([r["online"] for r in records])
    paired=[r for r in records if r["base"] is not None and r["online"] is not None]
    improved=sum(r["online"]<r["base"] for r in paired)
    result={"method":"MODEL_ONLY_TEACHER_FORCED_ANSWER_NLL","retrieval_used":False,
            "weights_accuracy_verified":False,"device":str(device),"base":base,"online":online,
            "paired":len(paired),"online_improved":improved,"records":records,
            "warning":"NLL on training-associated answers is NOT independent QA generalization."}
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="records"},ensure_ascii=False,indent=2))
    print("report:",dest)

if __name__=="__main__":main()
