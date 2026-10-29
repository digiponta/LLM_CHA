"""v0.13.58.66: Unknown gate audit.
No automated gold inference. Human-review label CSV must be explicitly APPROVED.
Unknown means 'no reusable answer in this 56-item library', not out-of-domain.
"""
import argparse,csv,json
from pathlib import Path
from train_daily_generation_v0135847 import dataset
from compare_japanese_semantic_v0135863 import MODEL,MODES,topk
from rerank_question_intent_v0135864 import rerank
from compare_retrieval_response_v0135865 import decide

def prepare(path,holdout):
    if path.exists():raise FileExistsError(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    cases=[(q["id"],q["user"],"KNOWN","PENDING","Existing development questions: do not use as independent final test") for q in holdout]
    cases += [(f"challenge-{i:02d}",q,"UNKNOWN","PENDING","Candidate unknown: verify no reusable training answer")
      for i,q in enumerate([
        "電子工作が楽しかったけれど、最後は失敗した",
        "前の話は終わりにして、新しい話題に変えたい",
        "日本で今日の為替レートはいくら？",
        "この写真の犬の犬種を教えて",
        "宇宙望遠鏡の最新の観測結果を教えて",
        "熱が高いので薬の量を決めて",
        "明日の東京の天気を予報して",
        "連立方程式を解いて、途中式も示して",
      ],1)]
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["id","question","expected","review_status","review_notes"])
        w.writeheader()
        for id,q,g,s,n in cases:w.writerow({"id":id,"question":q,"expected":g,"review_status":s,"review_notes":n})
    print(f"Prepared {len(cases)} dev cases; needs manual review: {path}")

def load_cases(path):
    with path.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
    if len(rows)<2:raise ValueError("need multiple cases")
    ids=set()
    for r in rows:
        if r["id"] in ids:raise ValueError("duplicate IDs")
        ids.add(r["id"])
        if not r["question"].strip() or r["expected"] not in ("KNOWN","UNKNOWN"):raise ValueError("invalid row")
        if r["review_status"]!="APPROVED":raise ValueError(f'{r["id"]}: review pending')
    if not any(r["expected"]=="KNOWN" for r in rows) or not any(r["expected"]=="UNKNOWN" for r in rows):
        raise ValueError("both classes required")
    return rows

def metrics(records):
    known=[r for r in records if r["expected"]=="KNOWN"]
    unknown=[r for r in records if r["expected"]=="UNKNOWN"]
    def rate(a):return sum(a)/len(a) if a else None
    return {"known_count":len(known),"unknown_count":len(unknown),
            "known_coverage":rate([r["accepted"] for r in known]),
            "known_accepted_top1_relevance":"NOT_LABELED",
            "unknown_reject_rate":rate([not r["accepted"] for r in unknown]),
            "unknown_false_accept_rate":rate([r["accepted"] for r in unknown])}
def audit(train,cases,embeddings,thresholds,penalties):
    results=[]
    for mode,penalty in penalties:
        ranked_cases=[]
        for q,hits in zip(cases,embeddings):
            ranked=rerank(q["question"],hits,*penalty) if mode=="intent" else [
                {**h,"adjusted_score":h["score"]} for h in hits]
            for threshold,margin in thresholds:
                d=decide(ranked,threshold,margin)
                ranked_cases.append({"id":q["id"],"question":q["question"],
                    "expected":q["expected"],"mode":mode,"threshold":threshold,
                    "margin":margin,"accepted":d["accepted"],"reason":d["reason"],
                    "top_hit":ranked[0]["id"],"top_question":ranked[0]["question"],
                    "top_score":ranked[0]["score"],"top_adjusted_score":ranked[0]["adjusted_score"]})
        for threshold,margin in thresholds:
            part=[r for r in ranked_cases if r["threshold"]==threshold and r["margin"]==margin]
            results.append({"mode":mode,"threshold":threshold,"margin":margin,
                            "metrics":metrics(part),"rows":part})
    return results

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_corrected_v0135849.jsonl"))
    p.add_argument("--cases",type=Path,default=Path("data/unknown_gate_dev_v0135866.csv"))
    p.add_argument("--output",type=Path,default=Path("results/unknown_gate_v0135866"))
    p.add_argument("--prepare",action="store_true")
    p.add_argument("--cpu",action="store_true")
    a=p.parse_args()
    train,held,_=dataset(a.source)
    if len(train)!=56 or len(held)!=8:raise ValueError("expected 56 train and 8 holdout")
    if a.prepare:return prepare(a.cases,held)
    if a.output.exists():raise FileExistsError(a.output)
    cases=load_cases(a.cases)
    import torch
    from sentence_transformers import SentenceTransformer
    m=SentenceTransformer(MODEL,device="cpu" if a.cpu or not torch.cuda.is_available() else "cuda",trust_remote_code=False)
    qp,dp=MODES["semantic"]
    index=m.encode([dp+r["user"] for r in train],normalize_embeddings=True)
    queries=m.encode([qp+r["question"] for r in cases],normalize_embeddings=True)
    hits=topk(queries,index,train,k=56)
    thresholds=[(.85,0),(.90,0),(.93,0),(.90,.01),(.90,.03)]
    results=audit(train,cases,hits,thresholds,[("ruri",(0,0)),("intent",(.12,.08))])
    a.output.mkdir(parents=True,exist_ok=False)
    payload={"version":"v0.13.58.66","type":"DEVELOPMENT_ONLY",
        "independent_test":False,"answer_quality_not_assessed":True,
        "known_labels_not_rank_relevance_labels":True,
        "score_not_probability":True,"thresholds_not_calibrated":True,
        "results":results}
    (a.output/"audit.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (a.output/"audit.csv").open("w",encoding="utf-8-sig",newline="") as f:
        cols=["mode","threshold","margin","id","question","expected","accepted","reason","top_hit","top_question","top_score","top_adjusted_score"]
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for arm in results:
            for row in arm["rows"]:w.writerow({k:row.get(k) for k in cols})
    for x in results:
        print(json.dumps({"mode":x["mode"],"threshold":x["threshold"],"margin":x["margin"],**x["metrics"]},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()
