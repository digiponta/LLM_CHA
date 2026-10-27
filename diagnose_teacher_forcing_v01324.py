"""v0.13.24 read-only teacher-forcing and prefix divergence diagnostics."""
import argparse
import json
from pathlib import Path

def first_divergence(reference,generated):
    for i,(a,b) in enumerate(zip(reference,generated)):
        if a!=b:return i
    return min(len(reference),len(generated)) if len(reference)!=len(generated) else None

def token_analysis(model,tokenizer,question,answer,prefix_tokens=8,max_tokens=64):
    import torch
    import torch.nn.functional as F
    prompt=tokenizer.encode("人: "+question+"\nAI: ",add_bos=True)
    target=tokenizer.encode(answer,add_eos=True)
    context=model.context_length
    if len(prompt)+len(target)>context+1:
        prompt=prompt[-max(1,context+1-len(target)):]
        target=target[:max(1,context+1-len(prompt))]
    inputs=(prompt+target)[:-1]
    start=len(prompt)-1
    device=next(model.parameters()).device
    with torch.no_grad():
        logits=model(torch.tensor([inputs],device=device))[0]
        logprobs=F.log_softmax(logits[start:start+len(target)],dim=-1)
        target_tensor=torch.tensor(target[:logprobs.size(0)],device=device)
        loss=-logprobs.gather(1,target_tensor[:,None]).squeeze(1)
        top1=logprobs.argmax(dim=-1)
        rank=(logprobs>logprobs.gather(1,target_tensor[:,None])).sum(dim=-1)+1
        # Greedy continuation is deliberately plain, no repetition penalty.
        def greedy(seed,n):
            ids=list(seed);out=[]
            for _ in range(n):
                x=torch.tensor([ids[-context:]],device=device)
                next_id=int(model(x)[0,-1].argmax().item())
                if next_id==tokenizer.eos_id:break
                ids.append(next_id);out.append(next_id)
            return out
        generated=greedy(prompt,min(max_tokens,len(target)))
        prefix=min(prefix_tokens,len(target))
        continuation=greedy(prompt+target[:prefix],min(max_tokens,len(target)-prefix))
    return {"teacher_forced_nll":float(loss.mean().item()),
            "teacher_forced_rank1_rate":float((rank==1).float().mean().item()),
            "first_target_rank":int(rank[0].item()),
            "first_target_probability":float(logprobs[0,target[0]].exp().item()),
            "target_tokens":len(target),
            "free_divergence":first_divergence(target,generated),
            "free_generated":tokenizer.decode(generated),
            "prefix_tokens":prefix,
            "prefix_divergence":first_divergence(target[prefix:],continuation),
            "prefix_continuation":tokenizer.decode(continuation),
            "free_token_ids":generated,
            "prefix_token_ids":continuation}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",type=Path,default=Path("model/model-gpu-v1.6.2-unapproved-qa-v01318.pt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--data",type=Path,default=Path("results/unapproved_stratified_pairs_v01318.jsonl"))
    p.add_argument("--output",type=Path,default=Path("results/teacher_forcing_v01324.json"))
    p.add_argument("--limit",type=int,default=16)
    p.add_argument("--prefix-tokens",type=int,default=8)
    a=p.parse_args()
    if a.limit<1 or a.prefix_tokens<0:p.error("invalid arguments")
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    from online_train import checkpoint_trained_fingerprints,pair_fingerprint
    from unapproved_corpus_learning_v0139 import load_jsonl
    import torch
    for path in (a.model,a.tokenizer,a.data):
        if not path.exists():p.error(f"missing {path}")
    bound=checkpoint_trained_fingerprints(a.model)
    rows=[r for r in load_jsonl(a.data) if pair_fingerprint(r["user"],r["assistant"]) in bound][:a.limit]
    if not rows:p.error("no checkpoint-bound examples")
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model,_=LanguageModel.load_checkpoint(str(a.model),device=device)
    model.eval()
    tokenizer=Tokenizer.load(str(a.tokenizer))
    details=[]
    for r in rows:
        m=token_analysis(model,tokenizer,r["user"],r["assistant"],a.prefix_tokens)
        details.append({"subject":r.get("subject"),"knowledge_id":r.get("knowledge_id"),**m})
    summary={"cases":len(details),
             "mean_teacher_forced_nll":sum(x["teacher_forced_nll"] for x in details)/len(details),
             "mean_rank1_rate":sum(x["teacher_forced_rank1_rate"] for x in details)/len(details),
             "first_token_rank1":sum(x["first_target_rank"]==1 for x in details),
             "free_first_token_match":sum(x["free_divergence"]!=0 for x in details),
             "prefix_first_token_match":sum(x["prefix_divergence"]!=0 for x in details)}
    report={"version":"v0.13.24","evaluation":"TRAINING_PAIRS_NOT_INDEPENDENT",
            "model":str(a.model),"summary":summary,"details":details,
            "production_unchanged":True}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print("report:",a.output)

if __name__=="__main__":main()
