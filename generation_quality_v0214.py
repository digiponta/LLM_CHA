"""v0.2.14: deterministic raw-generation benchmark, independent of chat gates.

Automated labels are *proxies*, not grammar judgments. Save every candidate for
manual ratings of naturalness, topicality, and content.
"""
from __future__ import annotations
import argparse,csv,json,re
from collections import Counter
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from conversation_diagnostics_v026 import classify_quality
from dialogue_state_v029 import normalize

def metrics(rows):
    n=len(rows)
    if not n:raise ValueError("empty generation set")
    answers=[r["generated"] for r in rows]
    generic=sum(classify_quality(r["prompt"].rsplit("人: ",1)[-1],r["generated"])["generic"] for r in rows)
    identical=sum(normalize(a)==normalize(b) for a,b in zip(answers,answers[1:]))
    invalid=sum(not a.strip() or len(a.strip())<3 for a in answers)
    distinct=len(set(answers))
    return {"count":n,"generic_fraction":round(generic/n,4),
            "adjacent_identical_fraction":round(identical/max(1,n-1),4),
            "empty_or_very_short_fraction":round(invalid/n,4),
            "distinct_response_fraction":round(distinct/n,4)}
def generate(model,tok,prompt,max_new_tokens):
    prefix=prompt+"\nAI: "
    ids=tok.encode(prefix)
    ids=model.generate(ids,max_new_tokens=max_new_tokens,eos_id=tok.eos_id,temperature=0,
                       repetition_penalty=1.15)
    answer=tok.decode(ids[len(tok.encode(prefix)):])
    # Text after role labels is not part of the first assistant response.
    return re.split(r"\n(?:人|AI):",answer,1)[0].strip()
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--models",nargs="+",default=["model/model-llm-cha-quality-v028.pt","model/model-llm-cha-dialogue-v0211.pt","model/model-llm-cha-generalization-v0212.pt"])
    p.add_argument("--dataset",default="data/dialogue_generalization_v0212/test.jsonl")
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--max-rows",type=int,default=30)
    p.add_argument("--max-new-tokens",type=int,default=60)
    p.add_argument("--output",default="results/generation_v0214.json")
    a=p.parse_args()
    dataset=[json.loads(s) for s in Path(a.dataset).read_text(encoding="utf-8").splitlines() if s.strip()]
    tok=Tokenizer.load(a.tokenizer);device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    report={}
    for model_path in a.models:
        model,_=LanguageModel.load_checkpoint(model_path,device);model.eval()
        records=[{"prompt":row["user"],"reference":row["assistant"],
                  "generated":generate(model,tok,row["user"],a.max_new_tokens)} for row in dataset[:a.max_rows]]
        report[model_path]={"metrics":metrics(records),"samples":records}
        del model
        if device.type=="cuda":torch.cuda.empty_cache()
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    manual=dest.with_suffix(".manual.csv")
    with manual.open("w",newline="",encoding="utf-8-sig") as handle:
        w=csv.writer(handle);w.writerow(["model","prompt","reference","generated","naturalness_1_to_5","topic_relevance_1_to_5","substantive_1_to_5"])
        for name,content in report.items():
            for row in content["samples"]:w.writerow([name,row["prompt"],row["reference"],row["generated"],"","",""])
    print(json.dumps({k:v["metrics"] for k,v in report.items()},ensure_ascii=False,indent=2))
    print("Manual rating sheet:",manual)
if __name__=="__main__":main()
