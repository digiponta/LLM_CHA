"""RSE Phase 1: select a corpus-grounded answer, no LLM expansion or training.

Only query text ranks candidates; answers are never injected into the ranker.
Unknown topics are explicitly abstained from using a configurable score threshold.
"""
import argparse,collections,json,math,re
from pathlib import Path

def terms(s):
    return re.findall(r"[一-龥]+|[ぁ-ゖ]+|[ァ-ヺー]+|[a-z0-9]+",s.lower())

def build(rows):
    docs=[]
    for i,x in enumerate(rows):
        q=x.get("user");a=x.get("assistant")
        if isinstance(q,str) and isinstance(a,str) and q.strip() and a.strip():
            docs.append({"id":i,"question":q.strip(),"answer":a.strip(),"tokens":terms(q)})
    return docs

def retrieve(docs,query,k=5):
    qt=set(terms(query))
    if not qt:return []
    df=collections.Counter(t for d in docs for t in set(d["tokens"]))
    n=len(docs)
    hits=[]
    for d in docs:
        dt=set(d["tokens"])
        shared=qt&dt
        if not shared:continue
        weight=sum(math.log((n+1)/(df[t]+1))+1 for t in shared)
        denom=sum(math.log((n+1)/(df[t]+1))+1 for t in qt)
        score=weight/denom if denom else 0
        hits.append({"id":d["id"],"score":round(score,6),"matched":sorted(shared),
                     "question":d["question"],"answer":d["answer"]})
    return sorted(hits,key=lambda d:(-d["score"],d["id"]))[:k]

def select(docs,query,min_score=0.65,k=5):
    candidates=retrieve(docs,query,k)
    if not candidates or candidates[0]["score"]<min_score:
        return {"status":"ABSTAIN","answer":None,"candidates":candidates,
                "expanded":False,"semantic_relevance_verified":False}
    return {"status":"SELECTED_REVIEW_REQUIRED","answer":candidates[0]["answer"],
            "selected_id":candidates[0]["id"],"candidates":candidates,
            "expanded":False,"semantic_relevance_verified":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",default="data/real_persona_pilot_v013588293.jsonl")
    p.add_argument("--question",required=True)
    p.add_argument("--threshold",type=float,default=0.65)
    p.add_argument("--top-k",type=int,default=5)
    p.add_argument("--report",default="results/rse_retrieval_v013588300.json")
    p.add_argument("--show-answers",action="store_true")
    a=p.parse_args()
    if not 0<=a.threshold<=1 or a.top_k<1:raise ValueError("invalid threshold or top-k")
    records=[json.loads(s) for s in Path(a.data).read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    out=select(build(records),a.question,a.threshold,a.top_k)
    # Default report omits verbatim conversational content from private corpus.
    safe={k:v for k,v in out.items() if k!="answer"}
    safe["candidates"]=[{"id":x["id"],"score":x["score"],"matched":x["matched"]} for x in out["candidates"]]
    target=Path(a.report);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(safe,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out if a.show_answers else safe,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
