"""v0.9.7.37: isolation of emotion and strategy conditioning effects.

Existing checkpoints stay frozen. Each semantic dimension is perturbed
separately; full text is saved for manual review.
"""
import argparse, collections, json
from pathlib import Path
import torch
from tokenizer_bpe import Tokenizer
from evaluate_emotion_generation_v09736 import build_cases, load, generate, SWAP
from train_emotion_conditioned_v09735 import semantic_prompt

STRATEGY_SWAP={
 "SHARE_JOY":"ACKNOWLEDGE_DISAPPOINTMENT",
 "GREET":"ACKNOWLEDGE_DISAPPOINTMENT",
 "IDENTITY_DIRECT":"ACKNOWLEDGE_DISAPPOINTMENT",
 "ACKNOWLEDGE_DISAPPOINTMENT":"SHARE_JOY",
 "ACKNOWLEDGE_NEGATED_SADNESS":"ACKNOWLEDGE_SADNESS",
 "ACKNOWLEDGE_MIXED":"SHARE_JOY",
}
def swap_strategy(s):
    return STRATEGY_SWAP.get(s,"ACKNOWLEDGE_DISAPPOINTMENT"
                            if s!="ACKNOWLEDGE_DISAPPOINTMENT" else "SHARE_JOY")

def prompts(q,emotion,strategy):
    other_emotion=SWAP[emotion]
    other_strategy=swap_strategy(strategy)
    return {
        "correct":semantic_prompt(q,emotion,strategy),
        "emotion_only_swapped":semantic_prompt(q,other_emotion,strategy),
        "strategy_only_swapped":semantic_prompt(q,emotion,other_strategy),
        "both_swapped":semantic_prompt(q,other_emotion,other_strategy),
    }

def diversity(texts):
    counts=collections.Counter(texts)
    return {"total":len(texts),"unique":len(counts),
            "top_response":counts.most_common(1)[0][0] if counts else None,
            "top_count":counts.most_common(1)[0][1] if counts else 0,
            "top_rate":round(counts.most_common(1)[0][1]/len(texts),4) if texts else 0}

def evaluate(model,tok,cases,runner=generate,seed=42):
    rows=[]
    for row in cases:
        variants=prompts(row["input"],row["emotion"],row["strategy"])
        outputs={key:runner(model,tok,prompt,seed) for key,prompt in variants.items()}
        correct=outputs["correct"]["text"]
        changes={key:outputs[key]["text"]!=correct for key in outputs if key!="correct"}
        rows.append({**row,"outputs":outputs,"changed_from_correct":changes,
                     "exact_reference":{key:(out["text"].strip()==row["reference"].strip())
                       if row["reference"] is not None else None for key,out in outputs.items()}})
    names=("correct","emotion_only_swapped","strategy_only_swapped","both_swapped")
    summary={name:{
        **diversity([r["outputs"][name]["text"] for r in rows]),
        "holdout_exact":sum(r["exact_reference"][name] is True for r in rows if r["source"]=="holdout"),
        "holdout_count":sum(r["source"]=="holdout" for r in rows)
    } for name in names}
    change_summary={name:sum(r["changed_from_correct"][name] for r in rows)
        for name in names if name!="correct"}
    return {"status":"DIAGNOSTIC_ONLY","case_count":len(rows),
            "summary":summary,"change_summary":change_summary,"rows":rows,
            "limitations":"Changed outputs do not establish correct semantic conditioning. Strategy/emotion marker swaps are deliberately contradictory, and observed development holdouts are not a blind final test.",
            "train_ready":False,"auto_promote":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--conditioned",required=True)
    p.add_argument("--tokenizer",required=True)
    p.add_argument("--output",default="results/emotion_ablation_v09737.json")
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--cpu",action="store_true")
    args=p.parse_args()
    output=Path(args.output)
    if output.exists():raise FileExistsError("Output already exists: "+str(output))
    device=torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda")
    tok=Tokenizer.load(args.tokenizer)
    model=load(args.conditioned,device,tok)
    result=evaluate(model,tok,build_cases(),seed=args.seed)
    result["checkpoint"]=args.conditioned
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({key:val for key,val in result.items() if key!="rows"},ensure_ascii=False,indent=2))
    print("report:",output)
if __name__=="__main__":main()
