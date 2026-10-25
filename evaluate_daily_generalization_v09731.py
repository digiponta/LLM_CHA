"""Evaluate held-out daily responses on untouched and SFT checkpoints.

No training; use identical decoding. Exact-match, expected-intent proxy and
human-review fields are separate, because lexical match is not fluency.
"""
import argparse,json,re
from pathlib import Path
import torch
from model import LanguageModel
from tokenizer_bpe import Tokenizer
from chat import generate_reply
from daily_conversation_foundation_v09728 import dataset

EXTRA=[
 {"id":"challenge-negation-1","input":"楽しくなかった","emotion":"DISAPPOINTMENT"},
 {"id":"challenge-negation-2","input":"悲しくないよ","emotion":"NON_SADNESS"},
 {"id":"challenge-mixed-1","input":"楽しかったけど少し残念だった","emotion":"MIXED"},
 {"id":"challenge-mixed-2","input":"疲れたけど満足した","emotion":"MIXED"},
 {"id":"challenge-sarcasm-1","input":"また失敗か、最高だね","emotion":"IRONY_AMBIGUOUS"},
 {"id":"challenge-topic-1","input":"あなたは誰ですか","emotion":"IDENTITY"},
 {"id":"challenge-topic-2","input":"こんにちは","emotion":"GREETING"}
]
SIGNALS={
 "POSITIVE":("良かった","嬉し","よかった","気に入"),
 "DISAPPOINTMENT":("残念","がっかり","期待"),
 "SADNESS":("悲し","つら","寂し"),
 "FATIGUE":("お疲れ","休"),
 "GRATITUDE":("どういたしまして","役に立"),
 "UNCERTAINTY":("困","迷","一緒に","気にな"),
}
def assess(answer,target,label):
    return {"target_exact":answer.strip()==target.strip(),
            "strategy_keyword_match":any(t in answer for t in SIGNALS.get(label,())),
            "human_review_required":True}
def load(path,device):
    p=Path(path)
    if not p.is_file():raise FileNotFoundError(str(p))
    model,_=LanguageModel.load_checkpoint(str(p),device=device)
    model.eval()
    return model
def evaluate(baseline,experimental,tokenizer,generate,holdout,challenge):
    if baseline.vocab_size!=tokenizer.vocab_size or experimental.vocab_size!=tokenizer.vocab_size:
        raise ValueError("Tokenizer/model vocabulary mismatch")
    rows=[]
    for row in holdout+challenge:
        question=row["input"]
        outputs={}
        for name,model in (("baseline",baseline),("experimental",experimental)):
            res=generate(model=model,tokenizer=tokenizer,
                         prompt="人: "+question+"\nAI: ",
                         max_new_tokens=64,temperature=0.0,
                         top_k=3,repetition_penalty=1.08,seed=42)
            answer=res.text
            entry={"answer":answer,"token_count":res.token_count,
                   "mean_confidence":res.mean_confidence,
                   "min_token_confidence":res.min_confidence}
            if "target" in row:
                entry.update(assess(answer,row["target"],row["semantic"]["emotion"]))
            outputs[name]=entry
        rows.append({"id":row["id"],"split":row.get("split","challenge"),
                     "input":question,"reference":row.get("target"),
                     "expected_emotion":row["semantic"]["emotion"] if "semantic" in row else row["emotion"],
                     "outputs":outputs})
    summary={}
    for name in ("baseline","experimental"):
        held=[r["outputs"][name] for r in rows if r["split"]=="holdout"]
        summary[name]={"holdout_count":len(held),
                       "exact_count":sum(x["target_exact"] for x in held),
                       "strategy_keyword_count":sum(x["strategy_keyword_match"] for x in held)}
    return {"status":"DIAGNOSTIC_ONLY","holdout_count":len(holdout),
            "challenge_count":len(challenge),"summary":summary,
            "rows":rows,"note":"Exact/keyword proxies are not semantic accuracy; manually review every response.",
            "train_ready":False,"auto_promote":False,"persisted":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--baseline",required=True)
    p.add_argument("--experimental",required=True)
    p.add_argument("--tokenizer",required=True)
    p.add_argument("--output",default="results/daily_generalization_v09731.json")
    p.add_argument("--cpu",action="store_true")
    args=p.parse_args()
    device=torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda")
    tok=Tokenizer.load(args.tokenizer)
    result=evaluate(load(args.baseline,device),load(args.experimental,device),
                    tok,generate_reply,dataset()["holdout"],EXTRA)
    result["models"]={"baseline":args.baseline,"experimental":args.experimental}
    path=Path(args.output)
    if path.exists():raise FileExistsError("Refusing to overwrite report: "+str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},ensure_ascii=False,indent=2))
    print("Report:",path)
if __name__=="__main__":main()
