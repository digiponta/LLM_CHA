"""v0.2.33.0: first-token, teacher forcing, prefix completion diagnostics.

No training, no automatic promotion; compare independently trained checkpoints.
"""
import argparse,json,math
from pathlib import Path
import torch
import torch.nn.functional as F
from dialogue_guided_generation_v02322 import CheckpointGenerator
from semantic_memory_expansion_v02328 import load_rows
from evaluate_semantic_transfer_v02327 import PROBES,prompt_for

def cases(path):
    rows=load_rows(path)
    approved=[r for r in rows if r["review_status"]=="APPROVED" and r["variant_type"]=="original"]
    if not approved:raise ValueError("No approved originals")
    out=[{"kind":"teacher","id":r["id"],"prompt":r["prompt"],"answer":r["answer"]} for r in approved]
    # Probes are untrained, but their reference answers are manual review targets,
    # NOT generated ground truth. Evaluate first-token NLL only on teachers.
    return out

def token_metrics(generator,prompt,answer):
    tok=generator.tokenizer;device=generator.device;model=generator.model
    p=tok.encode(prompt,add_bos=True);a=tok.encode(answer,add_eos=True)
    if len(p)+len(a)>model.context_length:
        raise ValueError("Sequence exceeds context; refuse silent truncation")
    ids=p+a
    x=torch.tensor([ids[:-1]],device=device,dtype=torch.long)
    with torch.inference_mode():
        logits=model(x)[0]
        selected=logits[len(p)-1:len(ids)-1]
        targets=torch.tensor(a,device=device,dtype=torch.long)
        logprobs=F.log_softmax(selected,dim=-1)
        nll=-logprobs.gather(-1,targets.unsqueeze(-1)).squeeze(-1)
        first_rank=int((selected[0]>selected[0,targets[0]]).sum().item()+1)
        first_prob=float(logprobs[0,targets[0]].exp().item())
        first_top=int(selected[0].argmax().item())
        return {"target_tokens":len(a),"teacher_nll":float(nll.mean().item()),
                "first_token_top1":first_top==a[0],
                "first_token_rank":first_rank,"first_token_probability":first_prob,
                "first_predicted_token":tok.decode([first_top]),
                "first_target_token":tok.decode([a[0]]),
                "first_five_nll":[round(float(v),5) for v in nll[:5].tolist()]}

def prefix_probe(generator,prompt,answer,fraction,max_new_tokens):
    tok=generator.tokenizer
    ans=tok.encode(answer)
    if len(ans)<2:raise ValueError("Answer too short for prefix test")
    n=max(1,min(len(ans)-1,math.ceil(len(ans)*fraction)))
    prefix=tok.decode(ans[:n],skip_special_tokens=True)
    result=generator.generate(prompt+prefix,max_new_tokens=max_new_tokens,temperature=0.0)
    return {"prefix_tokens":n,"prefix_text":prefix,"generated_continuation":result["text"],
            "expected_full_answer":answer,
            "note":"Compare manually: BPE decode/encode boundary may change when prefix is appended."}

def evaluate(models,test_cases,prefix_fraction=.25,max_new_tokens=80):
    data=[]
    for case in test_cases:
        row={**case,"models":{}}
        for name,g in models.items():
            row["models"][name]={
                "teacher_forcing":token_metrics(g,case["prompt"],case["answer"]),
                "free":g.generate(case["prompt"],max_new_tokens=max_new_tokens,temperature=0.0),
                "prefix":prefix_probe(g,case["prompt"],case["answer"],prefix_fraction,max_new_tokens)}
        data.append(row)
    return data

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--expansion",default="data/semantic_expansion_v02328.jsonl")
    p.add_argument("--base",default="model/model-llm-cha-response-quality-v0221.pt")
    p.add_argument("--original",default="model/model-llm-cha-memory-original-v02328.pt")
    p.add_argument("--expanded",default="model/model-llm-cha-memory-expanded-v02328.pt")
    p.add_argument("--tokenizer",default="model/tokenizer-v0.7-bpe.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--prefix-fraction",type=float,default=.25)
    p.add_argument("--max-new-tokens",type=int,default=80)
    p.add_argument("--out",default="results/internalization_diagnostics_v02330.json")
    args=p.parse_args()
    if not 0<args.prefix_fraction<1:raise ValueError("prefix-fraction must be between 0 and 1")
    generators={k:CheckpointGenerator(v,args.tokenizer,args.device) for k,v in
                (("base",args.base),("original",args.original),("expanded",args.expanded))}
    result=evaluate(generators,cases(args.expansion),args.prefix_fraction,args.max_new_tokens)
    dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps({"version":"v0.2.33.0","result":result,
        "warning":"Teacher metrics use training examples; diagnose token mechanics, not held-out generalization."},
        ensure_ascii=False,indent=2),encoding="utf-8")
    for row in result:
        print("[",row["id"],"]")
        for name,r in row["models"].items():
            m=r["teacher_forcing"]
            print(f"  {name}: first_top1={m['first_token_top1']} rank={m['first_token_rank']} p={m['first_token_probability']:.5f} teacher_nll={m['teacher_nll']:.4f}")
            print("    free:",repr(r["free"]["text"]))
            print("    prefix:",repr(r["prefix"]["prefix_text"]),"->",repr(r["prefix"]["generated_continuation"]))
    print("Saved:",dest)
if __name__=="__main__":main()
