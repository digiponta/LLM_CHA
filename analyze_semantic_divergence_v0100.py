"""Diagnose first greedy/reference token divergence under the actual model.

Uses model-only greedy output; reference rank is measured at the teacher-forced
prefix at the first divergence. Retrieval and training are not invoked.
"""
import argparse,json
from pathlib import Path

def first_difference(reference,generated):
    for i,(a,b) in enumerate(zip(reference,generated)):
        if a!=b:return i
    return min(len(reference),len(generated)) if len(reference)!=len(generated) else None

def inspect_case(model,tok,question,answer,max_new_tokens=96):
    import torch
    prompt=tok.encode("ユーザー: "+question+"\nAI: ",add_bos=True)
    target=tok.encode(answer,add_eos=True)
    if not prompt or not target:raise ValueError("Empty prompt or target")
    with torch.inference_mode():
        generated=model.generate(prompt,max_new_tokens=max_new_tokens,eos_id=tok.eos_id,
                                 temperature=0.0,top_k=None,repetition_penalty=1.05)
        completion=generated[len(prompt):]
        position=first_difference(target,completion)
        detail={"target_tokens":len(target),"generated_tokens":len(completion),
                "first_divergence_token":position,
                "matched_prefix_tokens":len(target) if position is None else position,
                "exact_token_sequence":position is None}
        if position is not None and position<len(target):
            context=(prompt+target[:position])[-model.context_length:]
            logits=model(torch.tensor([context],dtype=torch.long,device=next(model.parameters()).device))[0,-1].float()
            gold=target[position]
            # Greedy generation applies repetition penalty; use same decision rule.
            penalized=logits.clone()
            for token_id in set(prompt+target[:position]):
                if 0<=token_id<penalized.numel():
                    if penalized[token_id]>=0:penalized[token_id]/=1.05
                    else:penalized[token_id]*=1.05
            rank=int((penalized>penalized[gold]).sum().item())+1
            detail.update({"reference_token_rank_at_divergence":rank,
                           "reference_token_probability_at_divergence":
                           float(torch.softmax(penalized,dim=-1)[gold].item()),
                           "greedy_token_id":completion[position] if position<len(completion) else None})
        else:
            detail["reference_token_rank_at_divergence"]=None
            detail["reference_token_probability_at_divergence"]=None
        return detail

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--generation-report",default="results/semantic_generation_v0100.json")
    p.add_argument("--tokenizer",required=True)
    p.add_argument("--base",default="model/model-llm-try-nagato-chat-v94.pt")
    p.add_argument("--online",default="model/model-gpu-v1.6.2-online.pt")
    p.add_argument("--limit",type=int,default=56)
    p.add_argument("--max-new-tokens",type=int,default=96)
    p.add_argument("--output",default="results/semantic_divergence_v0100.json")
    args=p.parse_args()
    if args.limit<1 or args.max_new_tokens<1:p.error("positive limits required")
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    data=json.loads(Path(args.generation_report).read_text(encoding="utf-8-sig"))
    if data.get("method")!="MODEL_ONLY_GREEDY_GENERATION":raise ValueError("Unsupported generation report")
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(args.tokenizer)
    models={}
    for label,path in (("base",args.base),("online",args.online)):
        model,_=LanguageModel.load_checkpoint(path,device=device)
        model.eval();models[label]=model
    rows=[]
    for record in data["records"][:args.limit]:
        entry={"concept":record["concept"]}
        for label,model in models.items():
            entry[label]=inspect_case(model,tok,record["question"],record["reference"],args.max_new_tokens)
        rows.append(entry)
    report={"method":"MODEL_ONLY_FIRST_TOKEN_DIVERGENCE","retrieval_used":False,
            "independence_attested":False,"cases":len(rows),"records":rows,
            "note":"Ranks reflect greedy generation with repetition penalty; source cases remain train-associated."}
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for label in models:
        positions=[r[label]["matched_prefix_tokens"] for r in rows]
        ranks=[r[label]["reference_token_rank_at_divergence"] for r in rows if r[label]["reference_token_rank_at_divergence"] is not None]
        print(label,{"mean_matched_prefix_tokens":sum(positions)/len(positions) if positions else None,
                     "first_divergence_rank1":sum(x==1 for x in ranks),
                     "cases":len(rows)})
    print("report:",target)

if __name__=="__main__":main()
