"""Evaluate raw greedy outputs for topic mention and response quality proxies.

Metrics are diagnostic proxies, not semantic understanding or factual accuracy.
"""
from __future__ import annotations
import argparse,json,re
from collections import defaultdict
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer

DEFAULT_MODELS={
"baseline":"model/model-llm-cha-v0227-baseline.pt",
"persistence":"model/model-llm-cha-context-persistence-v0228.pt",
}
def score(topic,answer,generated_tokens):
    norm=lambda s:re.sub(r"\s+","",s)
    text=norm(answer)
    topic_hit=norm(topic) in text
    generic=["そうですね","長門有希","よろしくお願いします","お疲れ","なるほど","はい。"]
    generic_only=any(text.startswith(x) for x in generic) and not topic_hit
    repeated=bool(re.search(r"(.{3,})\1{2,}",text))
    return {"topic_mention":topic_hit,"generic_without_topic":generic_only,
            "repeated_span":repeated,"generated_tokens":generated_tokens,
            "nonempty":bool(text)}
@torch.no_grad()
def evaluate_one(model,tok,prompt,max_new_tokens):
    prefix="人: "+prompt+"\nAI: "
    ids=tok.encode(prefix,add_bos=True)
    generated=model.generate(ids,max_new_tokens=max_new_tokens,
                             eos_id=tok.eos_id,temperature=0.0,
                             repetition_penalty=1.15)[len(ids):]
    return tok.decode(generated),len(generated)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--fixture",default="data/topic_grounded_v02290/eval.jsonl")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--model",action="append",help="NAME=CHECKPOINT")
    p.add_argument("--max-new-tokens",type=int,default=64)
    p.add_argument("--out",default="results/topic_grounded_eval_v02290.jsonl")
    a=p.parse_args()
    if a.max_new_tokens<1:p.error("max-new-tokens must be > 0")
    source=Path(a.fixture)
    if not source.is_file():p.error("fixture missing; first run prepare_topic_grounded_v02290.py")
    cases=[json.loads(line) for line in source.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    models=dict(DEFAULT_MODELS)
    if a.model:
        models={}
        for spec in a.model:
            name,sep,filepath=spec.partition("=")
            if not sep or not name or not filepath:p.error("expected NAME=CHECKPOINT")
            models[name]=filepath
    tok=Tokenizer.load(a.tokenizer)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    output=Path(a.out);output.parent.mkdir(parents=True,exist_ok=True)
    stats=defaultdict(lambda:{"count":0,"hits":0,"generic":0})
    with output.open("w",encoding="utf-8") as stream:
        for name,path in models.items():
            model,_=LanguageModel.load_checkpoint(path,device=device)
            model.eval()
            if model.vocab_size!=tok.vocab_size:raise ValueError("tokenizer/model vocab mismatch")
            for c in cases:
                answer,n=evaluate_one(model,tok,c["prompt"],a.max_new_tokens)
                metrics=score(c["topic"],answer,n)
                row={"model":name,**c,"raw_answer":answer,**metrics}
                stream.write(json.dumps(row,ensure_ascii=False)+"\n")
                k=(name,c["split"])
                stats[k]["count"]+=1
                stats[k]["hits"]+=int(metrics["topic_mention"])
                stats[k]["generic"]+=int(metrics["generic_without_topic"])
                print(f'{name} {c["split"]} {c["topic"]}: {answer!r} mention={metrics["topic_mention"]}')
    for (name,split),s in stats.items():
        print(f'{name}/{split}: topic_mentions={s["hits"]}/{s["count"]}, '
              f'generic_without_topic={s["generic"]}/{s["count"]}')
    print("Saved:",output)
if __name__=="__main__":main()
