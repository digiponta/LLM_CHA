"""RSE phase 1.1: morphology-aware retrieval with hard content-term coverage.

Diagnostic only; never exposes or automatically outputs source speaker responses.
"""
import argparse,collections,json,math
from pathlib import Path

STOP={"は","が","の","に","を","で","と","も","へ","ね","よ","か","です","ます","だ","いる","ある","する","こと","もの","これ","それ","あれ","どう","何","今日","今","最近","？","?","。"}
def keywords(text,tokenizer):
    out=[]
    for m in tokenizer.tokenize(text):
        x=m.dictionary_form()
        pos=m.part_of_speech()[0]
        if x in STOP or len(x)==1 or pos in ("助詞","助動詞","補助記号","記号"):continue
        if pos in ("名詞","動詞","形容詞","副詞"):out.append(x)
    return list(dict.fromkeys(out))
def index(rows,tokenizer):
    return [{"id":i,"q":r["user"],"a":r["assistant"],"keys":keywords(r["user"],tokenizer)}
            for i,r in enumerate(rows) if isinstance(r.get("user"),str) and isinstance(r.get("assistant"),str)]
def search(rows,question,tokenizer,top_k=5,min_coverage=1.0,min_score=0.25):
    q=keywords(question,tokenizer)
    if not q:
        return {"status":"ABSTAIN","reason":"NO_CONTENT_TERMS","query_keywords":[],"candidates":[],"expansion":False}
    df=collections.Counter(t for r in rows for t in set(r["keys"]))
    n=len(rows);hits=[]
    denominator=sum(math.log(1+(n+1)/(df[t]+1)) for t in q)
    for row in rows:
        shared=set(q)&set(row["keys"])
        if not shared:continue
        coverage=len(shared)/len(q)
        score=sum(math.log(1+(n+1)/(df[t]+1)) for t in shared)/denominator
        hits.append({"id":row["id"],"score":round(score,5),"content_coverage":round(coverage,5),"matched":sorted(shared)})
    hits.sort(key=lambda x:(-x["content_coverage"],-x["score"],x["id"]))
    eligible=[x for x in hits if x["content_coverage"]>=min_coverage and x["score"]>=min_score]
    return {"status":"SELECTED_REVIEW_REQUIRED" if eligible else "ABSTAIN",
            "reason":"CONTENT_MATCH" if eligible else "CONTENT_COVERAGE_INSUFFICIENT",
            "query_keywords":q,"selected_id":eligible[0]["id"] if eligible else None,
            "candidates":hits[:top_k],"expansion":False,"semantic_relevance_verified":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",default="data/real_persona_pilot_v013588293.jsonl")
    p.add_argument("--question",required=True)
    p.add_argument("--output",default="results/rse_content_terms_v013588301.json")
    p.add_argument("--top-k",type=int,default=5)
    a=p.parse_args()
    from sudachipy import dictionary
    tokenizer=dictionary.Dictionary().tokenizer()
    rows=[json.loads(x) for x in Path(a.data).read_text(encoding="utf-8-sig").splitlines() if x.strip()]
    report=search(index(rows,tokenizer),a.question,tokenizer,a.top_k)
    output=Path(a.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
