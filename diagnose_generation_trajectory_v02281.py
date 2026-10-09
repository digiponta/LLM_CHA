"""v0.2.28.1: counterfactual generation trajectory diagnosis.

Only raw LanguageModel.generate; no runtime gate. Prefix forcing is a diagnostic
intervention, not evidence the model would have generated the forced tokens.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from analyze_initiation_distribution_v02272 import CASES, prompts

MODELS = {
    "baseline": "model/model-llm-cha-v0227-baseline.pt",
    "selective": "model/model-llm-cha-context-selective-v02271.pt",
    "persistence": "model/model-llm-cha-context-persistence-v0228.pt",
}

def make_conditions(reference_ids, first_k):
    if not reference_ids:
        raise ValueError("empty reference")
    if first_k < 1:
        raise ValueError("first_k must be positive")
    # Half is a fixed token prefix, not half of the number of words.
    half = max(1, len(reference_ids) // 2)
    return [("free", []),
            ("first_k", reference_ids[:min(first_k, len(reference_ids))]),
            ("first_half", reference_ids[:half])]

@torch.no_grad()
def generate_one(model, tokenizer, prompt, reference, max_new_tokens, first_k):
    prompt_ids = tokenizer.encode(prompt, add_bos=True)
    reference_ids = tokenizer.encode(reference, add_eos=False)
    if len(prompt_ids) + len(reference_ids) > model.context_length:
        raise ValueError("Prompt/reference exceed context; refusing silent truncation")
    result = []
    for condition, forced in make_conditions(reference_ids, first_k):
        # Budget counts the generated continuation, not the forced prefix.
        start = prompt_ids + forced
        full = model.generate(start, max_new_tokens=max_new_tokens,
                              eos_id=tokenizer.eos_id,
                              temperature=0.0, repetition_penalty=1.15)
        continuation = full[len(start):]
        complete = full[len(prompt_ids):]
        result.append({
            "condition": condition,
            "forced_token_count": len(forced),
            "forced_text": tokenizer.decode(forced),
            "continuation_text": tokenizer.decode(continuation),
            "complete_answer": tokenizer.decode(complete),
            "generated_token_count": len(continuation),
            "eos_generated": bool(continuation and continuation[-1] == tokenizer.eos_id),
        })
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", action="append", help="NAME=CHECKPOINT; repeatable")
    p.add_argument("--tokenizer", default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--first-k",type=int,default=8)
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--out",default="results/generation_trajectory_v02281.jsonl")
    a=p.parse_args()
    if min(a.first_k,a.max_new_tokens)<1:p.error("token counts must be positive")
    models=dict(MODELS)
    if a.model:
        models={}
        for s in a.model:
            name,sep,path=s.partition("=")
            if not sep or not name or not path:p.error("--model NAME=CHECKPOINT")
            models[name]=path
    tokenizer=Tokenizer.load(a.tokenizer)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    output=Path(a.out);output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("w",encoding="utf-8") as f:
        for name,path in models.items():
            model,_=LanguageModel.load_checkpoint(path,device=device)
            model.eval()
            if model.vocab_size!=tokenizer.vocab_size:raise ValueError("vocabulary mismatch")
            for case in CASES:
                for form,prompt in prompts(case).items():
                    for item in generate_one(model,tokenizer,prompt,case["target"],
                                             a.max_new_tokens,a.first_k):
                        row={"model":name,"checkpoint":path,"topic":case["topic"],
                             "prompt_format":form,"reference":case["target"],**item}
                        print(json.dumps(row,ensure_ascii=False))
                        f.write(json.dumps(row,ensure_ascii=False)+"\n")
    print("Saved:",output)

if __name__=="__main__":main()
