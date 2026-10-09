"""v0.2.27.2 first-token distribution and prompt alignment diagnostic.

Measure raw model distributions without chat gates. No forced topic copying.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

import torch
import torch.nn.functional as F
from model import LanguageModel
from tokenizer_bpe import Tokenizer

MODELS = {
    "baseline": "model/model-llm-cha-v0227-baseline.pt",
    "init_all": "model/model-llm-cha-v0227-init-k8.pt",
    "init_selective": "model/model-llm-cha-context-selective-v02271.pt",
}
CASES = [
    {"id":"space","topic":"宇宙探査","category":"SF小説",
     "target":"宇宙探査の物語では、未知の惑星や乗組員の選択が見どころになるね。"},
    {"id":"curry","topic":"カレー","category":"料理",
     "target":"カレーなら、野菜や香辛料の組み合わせで味の変化を楽しめるね。"},
    {"id":"mint","topic":"ミント","category":"園芸",
     "target":"ミントの栽培では、葉の香りや成長の変化を観察できるね。"},
]
def prompts(case):
    topic, category = case["topic"], case["category"]
    return {
        "single": f"人: {topic}について話を続けて\nAI: ",
        "training_format": (
            f"人: 最近、{category}に興味があります\n"
            f"AI: どんなことに興味があるの？\n"
            f"人: {topic}です\nAI: その話を聞かせて\n"
            "人: その話を続けて\nAI: "
        ),
    }

@torch.no_grad()
def measure(model, tokenizer, text, target, max_length):
    ids = tokenizer.encode(text, add_bos=True)
    target_ids = tokenizer.encode(target, add_eos=True)
    if len(ids) > max_length:
        raise ValueError("Prompt longer than context_length; refusing silent truncation")
    x = torch.tensor([ids], dtype=torch.long, device=next(model.parameters()).device)
    probs = F.softmax(model(x)[0,-1,:].float(), dim=-1)
    top = torch.topk(probs, k=10)
    first_id = target_ids[0]
    rank = int((probs > probs[first_id]).sum().item()) + 1
    p = float(probs[first_id].item())
    entropy = float((-(probs * probs.clamp_min(1e-30).log()).sum()).item())
    return {
        "target_first_token": tokenizer.decode([first_id],skip_special_tokens=False),
        "target_first_token_id": first_id,
        "target_probability": p,
        "target_rank": rank,
        "top1_is_target": int(top.indices[0].item()) == first_id,
        "entropy_nats": entropy,
        "top10": [
            {"id":int(i),"token":tokenizer.decode([int(i)],skip_special_tokens=False),
             "probability":float(v)}
            for i,v in zip(top.indices.tolist(),top.values.tolist())
        ],
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    ap.add_argument("--out",default="results/init_distribution_v02272.jsonl")
    ap.add_argument("--model",action="append",help="Optional NAME=CHECKPOINT, repeatable")
    args=ap.parse_args()
    models=dict(MODELS)
    if args.model:
        models={}
        for entry in args.model:
            name,sep,path=entry.partition("=")
            if not sep or not name or not path:ap.error("Use --model NAME=CHECKPOINT")
            models[name]=path
    tokenizer=Tokenizer.load(args.tokenizer)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    records=[]
    for name,path in models.items():
        model,_=LanguageModel.load_checkpoint(path,device=device)
        model.eval()
        if model.vocab_size!=tokenizer.vocab_size:raise ValueError("Vocab mismatch")
        for case in CASES:
            for form,text in prompts(case).items():
                record={"model":name,"checkpoint":path,"case":case["id"],"topic":case["topic"],
                        "format":form,"prompt":text,
                        **measure(model,tokenizer,text,case["target"],model.context_length)}
                records.append(record)
                print(f'{name:15} {case["id"]:6} {form:15} p={record["target_probability"]:.6f} rank={record["target_rank"]} entropy={record["entropy_nats"]:.3f}')
    outfile=Path(args.out);outfile.parent.mkdir(parents=True,exist_ok=True)
    with outfile.open("w",encoding="utf-8") as f:
        for record in records:f.write(json.dumps(record,ensure_ascii=False)+"\n")
    print("Saved:",outfile)
if __name__=="__main__":main()
