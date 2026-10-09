"""v0.2.23 evaluation: matched-context reference NLL matrix.

Diagonal cells use matching context/answer, off-diagonal swap the context
but keep the target answer. Diagonal advantage >0 is evidence the model
conditions answer likelihood on the proper topic. No training here.
"""
import argparse,json
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from diagnose_models_v0213 import score_answer
from prepare_context_conditional_v0223 import TOPICS,HOLDOUT,make

def matrix(model,tok,topics):
    rows=[make(t) for t in topics]
    vals=[]
    for target in rows:
        col=[]
        for context in rows:
            result=score_answer(model,tok,context["user"],target["assistant"])
            if not result:raise ValueError("Failed to score reference")
            col.append(round(result[0]/result[1],5))
        vals.append(col)
    margins=[round(min(v for j,v in enumerate(row) if j!=i)-row[i],5) for i,row in enumerate(vals)]
    return {"topics":[t[0] for t in topics],"nll_target_by_context":vals,
            "diagonal_margin_vs_best_wrong":margins,
            "diagonal_best_fraction":round(sum(m>0 for m in margins)/len(margins),4),
            "mean_diagonal_margin":round(sum(margins)/len(margins),5)}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--models",nargs="+",default=["model/model-llm-cha-response-quality-v0221.pt","model/model-llm-cha-context-conditional-v0223.pt"])
    p.add_argument("--tokenizer",default="../LLM_TRY/model/tokenizer-v0.7-bpe.json")
    p.add_argument("--output",default="results/context_conditioning_v0223.json")
    a=p.parse_args()
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tok=Tokenizer.load(a.tokenizer);reports={}
    for path in a.models:
        model,_=LanguageModel.load_checkpoint(path,device);model.eval()
        reports[path]={"train_topics":matrix(model,tok,TOPICS),"holdout_topics":matrix(model,tok,HOLDOUT)}
        del model
        if device.type=="cuda":torch.cuda.empty_cache()
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(reports,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:{s:{"diagonal_best_fraction":x["diagonal_best_fraction"],"mean_diagonal_margin":x["mean_diagonal_margin"]} for s,x in v.items()} for k,v in reports.items()},ensure_ascii=False,indent=2))
    print("Full matrix:",dest)
if __name__=="__main__":main()
