"""Matched four-arm generation comparison; no training."""
import argparse,json,collections
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from chat import generate_reply
from evaluate_emotion_generation_v09736 import build_cases
from train_emotion_factorial_v09738 import ARMS,prompt

def summarize(texts):
    c=collections.Counter(texts)
    return {"unique":len(c),"top_response":c.most_common(1)[0][0],
            "top_count":c.most_common(1)[0][1],"total":len(texts)}
def evaluate(models,tok,cases,seed=42,generator=generate_reply):
    rows=[]
    for r in cases:
        outputs={}
        for arm in ARMS:
            result=generator(models[arm],tok,prompt(r["input"],r["emotion"],r["strategy"],arm),
              max_new_tokens=48,temperature=0.0,top_k=3,repetition_penalty=1.08,seed=seed)
            outputs[arm]={"text":result.text,
                "reference_exact":None if r["reference"] is None else result.text.strip()==r["reference"].strip()}
        rows.append({"id":r["id"],"source":r["source"],"emotion":r["emotion"],
          "input":r["input"],"reference":r["reference"],"outputs":outputs})
    summary={}
    for arm in ARMS:
        summary[arm]={**summarize([r["outputs"][arm]["text"] for r in rows]),
          "holdout_exact":sum(r["outputs"][arm]["reference_exact"] is True for r in rows),
          "holdout_count":sum(r["source"]=="holdout" for r in rows)}
    return {"status":"DIAGNOSTIC_ONLY","case_count":len(rows),"summary":summary,"rows":rows,
       "note":"Reference exact match is not a semantic correctness score; inspect full texts. Holdout was previously inspected and is not a blind final test.",
       "train_ready":False,"auto_promote":False}
def main():
    p=argparse.ArgumentParser()
    for arm in ARMS:p.add_argument("--"+arm,required=True)
    p.add_argument("--tokenizer",required=True)
    p.add_argument("--output",default="results/emotion_factorial_v09738.json")
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--cpu",action="store_true")
    a=p.parse_args()
    output=Path(a.output)
    if output.exists():raise FileExistsError(str(output))
    device=torch.device("cpu" if a.cpu or not torch.cuda.is_available() else "cuda")
    tok=Tokenizer.load(a.tokenizer)
    models={}
    for arm in ARMS:
        model,_=LanguageModel.load_checkpoint(getattr(a,arm),device=device)
        if model.vocab_size!=tok.vocab_size:raise ValueError("vocab mismatch")
        model.eval();models[arm]=model
    result=evaluate(models,tok,build_cases(),seed=a.seed)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},ensure_ascii=False,indent=2))
    print("report:",output)
if __name__=="__main__":main()
