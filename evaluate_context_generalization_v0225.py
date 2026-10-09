"""v0.2.25 combined topic-generalization + raw Japanese generation diagnostics.

Generates identical prompts for all checkpoints, matrix NLL and Greedy text.
Lexical topic hit is only a proxy; review output manually before adoption.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from diagnose_models_v0213 import score_answer
from diagnose_eos_decoding_v0216 import decode_trace
from prepare_context_generalization_v0225 import TRAIN,HOLDOUT,make

def score_set(model,tok,topics,max_new_tokens=60):
    rows=[make(t) for t in topics];records=[]
    for i,row in enumerate(rows):
        answer=row["assistant"];other=[]
        correct=score_answer(model,tok,row["user"],answer)
        if not correct:raise ValueError("Could not score target")
        for j,r in enumerate(rows):
            if j==i:continue
            score=score_answer(model,tok,r["user"],answer)
            if score:other.append(score[0]/score[1])
        margin=min(other)-correct[0]/correct[1]
        generated=decode_trace(model,tok,row["user"],temperature=0,top_k=40,seed=42,max_new_tokens=max_new_tokens)["generated"]
        tokens=re.findall(r"[一-龥ァ-ヶー]{2,}|[A-Za-z]{2,}",topics[i][1])
        hits=[w for w in tokens if w in generated]
        records.append({"topic":topics[i][0],"focus":topics[i][1],"prompt":row["user"],"reference":answer,
                        "context_margin":round(margin,5),"generated":generated,"topic_hits":hits,
                        "short_reply":len(generated.rstrip("。！？!? "))<8})
    return {"count":len(records),"diagonal_best_fraction":round(sum(r["context_margin"]>0 for r in records)/len(records),4),
            "mean_margin":round(sum(r["context_margin"] for r in records)/len(records),5),
            "topic_keyword_hit_fraction":round(sum(bool(r["topic_hits"]) for r in records)/len(records),4),
            "short_reply_fraction":round(sum(r["short_reply"] for r in records)/len(records),4),"records":records}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--models",nargs="+",default=["model/model-llm-cha-response-quality-v0221.pt","model/model-llm-cha-context-weighted-v0224.pt","model/model-llm-cha-context-generalization-v0225.pt"])
 p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
 p.add_argument("--output",default="results/context_generalization_v0225.json")
 a=p.parse_args();tok=Tokenizer.load(a.tokenizer)
 device=torch.device("cuda" if torch.cuda.is_available() else "cpu");data={}
 for path in a.models:
  model,_=LanguageModel.load_checkpoint(path,device);model.eval()
  data[path]={"train":score_set(model,tok,TRAIN),"unseen":score_set(model,tok,HOLDOUT)}
  del model
  if device.type=="cuda":torch.cuda.empty_cache()
 out={"models":data,"note":"Synthetic topic holdout, lexical hits and shortness are proxies, not independent Japanese fluency ratings."}
 target=Path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
 target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({m:{s:{k:v[k] for k in ("count","diagonal_best_fraction","mean_margin","topic_keyword_hit_fraction","short_reply_fraction")} for s,v in values.items()} for m,values in data.items()},ensure_ascii=False,indent=2))
 print("Review generated text:",target)
if __name__=="__main__":main()
