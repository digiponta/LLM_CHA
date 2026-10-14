#!/usr/bin/env python3
"""LLM_CHA v0.4.28.54: raw model generation A/B (full context vs last user).

This is a diagnostic experiment, NOT production chat runtime evaluation.
Both arms share model, checkpoint, prompt suffix, seed and decode parameters.
"""
import argparse
import hashlib
import json
import random
from pathlib import Path

VERSION="v0.4.28.54"

def make_prompt(text):
    return text.rstrip()+"\n相手: "

def run_experiment(data, model, tokenizer, *, device, max_new_tokens=64,
                   temperature=0.45, top_k=20, repetition_penalty=1.05,
                   seed=42854, limit=None):
    import torch
    if data.get("version")!="v0.4.28.53" or data.get("train_ready") is not False:
        raise ValueError("unsafe/unsupported ablation dataset")
    examples=data["examples"]
    if limit is not None:
        if limit<1: raise ValueError("limit must be positive")
        examples=examples[:limit]
    results=[]
    for i,row in enumerate(examples):
        if row.get("train_eligible") is not False: raise ValueError("train_eligible must be false")
        pair={"id":row["id"],"source_line":row.get("source_line"),"variants":{}}
        for arm,field in (("full_context","full_context"),("last_user_only","last_user_only")):
            prompt_text=row.get(field)
            if not isinstance(prompt_text,str) or not prompt_text.strip():
                pair["variants"][arm]={"status":"not_applicable","reason":"invalid conversation format"}
                continue
            text=make_prompt(prompt_text)
            input_ids=tokenizer.encode(text,add_bos=True)
            if not input_ids: raise ValueError("empty encoded prompt")
            random.seed(seed+i)
            torch.manual_seed(seed+i)
            if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed+i)
            with torch.no_grad():
                full_ids=model.generate(input_ids,max_new_tokens=max_new_tokens,
                     eos_id=tokenizer.eos_id,temperature=temperature,
                     top_k=top_k,repetition_penalty=repetition_penalty)
            gen_ids=full_ids[len(input_ids):]
            response=tokenizer.decode(gen_ids).split("\n人:")[0].split("\n相手:")[0].strip()
            pair["variants"][arm]={
                "status":"generated","response":response,
                "prompt_tokens":len(input_ids),"generated_tokens":len(gen_ids),
                "nonempty":bool(response),"raw_model":True}
        results.append(pair)
    both=sum(all(x["variants"][k].get("status")=="generated"
        for k in ("full_context","last_user_only")) for x in results)
    return {"version":VERSION,"mode":"RAW_MODEL_ABLATION",
        "checkpoint_comparison":"identical", "device":str(device),
        "sampling_seed_per_pair":seed,"max_new_tokens":max_new_tokens,
        "temperature":temperature,"top_k":top_k,"repetition_penalty":repetition_penalty,
        "examples_evaluated":len(results),"paired_generations":both,
        "reference_responses_used_for_generation":False,
        "quality_ratings":None,"accuracy":None,
        "results":results,"accepted":0,"human_verified":False,
        "train_ready":False,"runtime_modified":False,
        "note":"Generation outputs are raw samples only. Relevance and quality require independent blind review."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",required=True)
    p.add_argument("--model",required=True,help="Existing LLM_CHA checkpoint path")
    p.add_argument("--tokenizer",required=True)
    p.add_argument("--output",default="results/raw_generation_ablation_v042854.json")
    p.add_argument("--device",choices=("auto","cpu","cuda"),default="auto")
    p.add_argument("--limit",type=int,default=50)
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--seed",type=int,default=42854)
    args=p.parse_args()
    import torch
    from model import LanguageModel
    from tokenizer_bpe import Tokenizer
    device=torch.device("cuda" if (args.device=="auto" and torch.cuda.is_available()) else
                        "cpu" if args.device=="auto" else args.device)
    model,checkpoint=LanguageModel.load_checkpoint(args.model,device=device)
    tokenizer=Tokenizer.load(args.tokenizer)
    if model.vocab_size!=tokenizer.vocab_size:raise ValueError("model/tokenizer vocab mismatch")
    source=Path(args.input)
    destination=Path(args.output)
    if source.resolve()==destination.resolve():raise ValueError("input/output must differ")
    data=json.loads(source.read_text(encoding="utf-8"))
    result=run_experiment(data,model,tokenizer,device=device,limit=args.limit,seed=args.seed,max_new_tokens=args.max_new_tokens)
    result["model_path"]=str(Path(args.model))
    result["model_sha256"]=hashlib.file_digest(open(args.model,"rb"),"sha256").hexdigest()
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("version","mode","examples_evaluated","paired_generations","quality_ratings","train_ready","runtime_modified")},ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
