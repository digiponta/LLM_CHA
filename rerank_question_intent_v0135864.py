"""v0.13.58.64 intent-aware reranking of existing semantic retrieval.

Development-only heuristic. Does not claim learned semantic understanding.
Reranks a configurable Top-N candidate list, never changes embeddings.
Features are deliberately published and auditable.
"""
import argparse,csv,json,re
from pathlib import Path
from train_daily_generation_v0135847 import dataset
from compare_japanese_semantic_v0135863 import MODEL,MODES,topk

def intent(s):
    s=str(s)
    if re.search(r"別の話|ほかの話|他の話|話題を変|話を変",s):return "CHANGE_TOPIC"
    if re.search(r"続き|話に戻|前の話|さっきの話",s):return "CONTINUE_TOPIC"
    return "OTHER"
def valence(s):
    s=str(s)
    if re.search(r"失敗|うまくいかな|思い通りに進まな|集中できな|疲れ|眠た|眠く|落ち込",s):return "DIFFICULTY"
    if re.search(r"楽しい|うれしい|嬉しい|うまくいった|うまくいって|成功",s):return "POSITIVE"
    return "UNKNOWN"
def rerank(query,hits,intent_penalty=.12,valence_penalty=.08):
    qi,qv=intent(query),valence(query)
    output=[]
    for hit in hits:
        ci,cv=intent(hit["question"]),valence(hit["question"])
        conflict=(qi,ci) in (("CHANGE_TOPIC","CONTINUE_TOPIC"),("CONTINUE_TOPIC","CHANGE_TOPIC"))
        mismatch=qv!="UNKNOWN" and cv!="UNKNOWN" and qv!=cv
        penalty=(intent_penalty if conflict else 0)+(valence_penalty if mismatch else 0)
        output.append({**hit,"original_rank":hit["rank"],"intent_query":qi,"intent_candidate":ci,
                       "valence_query":qv,"valence_candidate":cv,
                       "intent_conflict":conflict,"valence_conflict":mismatch,
                       "penalty":round(penalty,6),"adjusted_score":round(hit["score"]-penalty,6)})
    output.sort(key=lambda x:(-x["adjusted_score"],str(x["id"])))
    for i,r in enumerate(output):r["rank"]=i+1
    return output
def run(a):
    if a.output.exists():raise FileExistsError(a.output)
    train,holdout,_=dataset(a.source)
    if len(train)!=56 or len(holdout)!=8:raise ValueError("requires 56 train and 8 holdout")
    import torch
    from sentence_transformers import SentenceTransformer
    device="cpu" if a.cpu or not torch.cuda.is_available() else "cuda"
    model=SentenceTransformer(MODEL,device=device,trust_remote_code=False)
    # Main experiment uses symmetric sentence-to-sentence embeddings.
    qp,dp=MODES["semantic"]
    e_train=model.encode([dp+r["user"] for r in train],normalize_embeddings=True,batch_size=a.batch_size)
    e_hold=model.encode([qp+r["user"] for r in holdout],normalize_embeddings=True,batch_size=a.batch_size)
    results=[]
    for q,base in zip(holdout,topk(e_hold,e_train,train,k=a.candidates)):
        ranked=rerank(q["user"],base,a.intent_penalty,a.valence_penalty)
        results.append({"holdout_id":q["id"],"question":q["user"],
                        "baseline_top3":base[:3],"reranked_top3":ranked[:3],
                        "all_reranked":ranked})
    a.output.mkdir(parents=True,exist_ok=False)
    report={"version":"v0.13.58.64","model":MODEL,"candidate_count":a.candidates,
      "intent_penalty":a.intent_penalty,"valence_penalty":a.valence_penalty,
      "evaluation":"development reused holdout, non-independent",
      "rules_are_heuristic":True,"human_gold_evaluated":False,
      "warning":"Reranking parameters are tuned against previously inspected queries; no generalization claim.",
      "results":results}
    (a.output/"rerank.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (a.output/"rerank.csv").open("w",newline="",encoding="utf-8-sig") as f:
        fields=["holdout_id","query","mode","rank","original_rank","candidate_id","candidate","base_score","penalty","adjusted_score","intent_conflict","valence_conflict"]
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in results:
            for mode,items in (("baseline",r["baseline_top3"]),("reranked",r["reranked_top3"])):
                for h in items:
                    w.writerow({"holdout_id":r["holdout_id"],"query":r["question"],"mode":mode,
                       "rank":h["rank"],"original_rank":h.get("original_rank",h["rank"]),
                       "candidate_id":h["id"],"candidate":h["question"],"base_score":h["score"],
                       "penalty":h.get("penalty",0),"adjusted_score":h.get("adjusted_score",h["score"]),
                       "intent_conflict":h.get("intent_conflict",""),
                       "valence_conflict":h.get("valence_conflict","")})
    for r in results:
        print(f'{r["holdout_id"]}: {r["question"]}')
        print(" BASE:",[(h["question"],h["score"]) for h in r["baseline_top3"]])
        print(" NEW :",[(h["question"],h["adjusted_score"]) for h in r["reranked_top3"]])
    print("report:",a.output/"rerank.json")
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_corrected_v0135849.jsonl"))
    p.add_argument("--output",type=Path,default=Path("results/intent_rerank_v0135864"))
    p.add_argument("--candidates",type=int,default=56)
    p.add_argument("--intent-penalty",type=float,default=.12)
    p.add_argument("--valence-penalty",type=float,default=.08)
    p.add_argument("--batch-size",type=int,default=16)
    p.add_argument("--cpu",action="store_true")
    a=p.parse_args()
    if not 3<=a.candidates<=56 or not 0<=a.intent_penalty<=1 or not 0<=a.valence_penalty<=1:
        p.error("invalid candidate count or penalty")
    run(a)
if __name__=="__main__":main()
