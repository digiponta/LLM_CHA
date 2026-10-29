"""v0.13.58.61 - Holdout -> training question Top-3 retrieval.
No model change; lexical char ngram and char TF-IDF baselines.
Only training split enters retrieval index. No reference answer in ranking.
"""
import argparse,csv,html,json,math,re,collections
from pathlib import Path
from train_daily_generation_v0135847 import dataset

def norm(s):
    import unicodedata
    return re.sub(r"\s+","",unicodedata.normalize("NFKC",str(s)).lower())
def grams(s,n):
    s=norm(s)
    return collections.Counter(s[i:i+n] for i in range(max(0,len(s)-n+1))) if len(s)>=n else collections.Counter([s] if s else [])
def cos(a,b):
    return sum(v*b.get(k,0) for k,v in a.items())/math.sqrt(sum(x*x for x in a.values())*sum(x*x for x in b.values())) if a and b else 0.
def index(rows,n=2,method="tfidf"):
    docs=[grams(r["user"],n) for r in rows]
    if method=="tfidf":
        df=collections.Counter(k for d in docs for k in d)
        idf={k:math.log((1+len(docs))/(1+v))+1 for k,v in df.items()}
    else:idf={}
    def vector(c):
        return {k:(1+math.log(v))*idf.get(k,math.log(1+len(docs))+1) if method=="tfidf" else float(v) for k,v in c.items()}
    return [vector(c) for c in docs],vector
def retrieve(train,query,n=2,method="tfidf",k=3):
    vectors,encode=index(train,n,method)
    q=encode(grams(query,n))
    order=sorted(range(len(train)),key=lambda i:(-cos(q,vectors[i]),str(train[i]["id"])))
    return [{"rank":j+1,"id":train[i]["id"],"question":train[i]["user"],
             "answer":train[i]["assistant"],"score":round(cos(q,vectors[i]),6)}
             for j,i in enumerate(order[:k])]
def execute(source,output,methods,ngrams):
    if output.exists():raise FileExistsError(output)
    train,holdout,protected=dataset(source)
    if not train or not holdout:raise ValueError("empty split")
    if {x["id"] for x in train}&{x["id"] for x in holdout}:raise ValueError("id split overlap")
    if {norm(x["user"]) for x in train}&{norm(x["user"]) for x in holdout}:raise ValueError("question leakage")
    records=[]
    for method in methods:
        for n in ngrams:
            for q in holdout:
                records.append({"method":method,"ngram":n,"holdout_id":q["id"],
                  "holdout_question":q["user"],"holdout_reference_answer":q["assistant"],
                  "top3":retrieve(train,q["user"],n,method)})
    output.mkdir(parents=True,exist_ok=False)
    (output/"top3.json").write_text(json.dumps({"version":"v0.13.58.61","train_count":len(train),"holdout_count":len(holdout),
          "methods":methods,"ngrams":ngrams,"results":records,"ground_truth_similarity_labels":False,
          "note":"Similarity score is lexical retrieval, not semantic correctness."},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (output/"top3.csv").open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=["method","ngram","holdout_id","holdout_question","rank","score","train_id","train_question","train_answer","human_relevance"])
        writer.writeheader()
        for record in records:
            for hit in record["top3"]:
                writer.writerow({"method":record["method"],"ngram":record["ngram"],"holdout_id":record["holdout_id"],
                      "holdout_question":record["holdout_question"],"rank":hit["rank"],"score":hit["score"],
                      "train_id":hit["id"],"train_question":hit["question"],"train_answer":hit["answer"],"human_relevance":""})
    cards=[]
    for r in records:
        hits="".join("<li><strong>#%d</strong> <code>%.4f</code> %s <small>[%s]</small></li>"%
           (h["rank"],h["score"],html.escape(h["question"]),html.escape(str(h["id"]))) for h in r["top3"])
        cards.append('<section><small>%s · char-%d · %s</small><h3>%s</h3><ol>%s</ol></section>'%
          (html.escape(r["method"]),r["ngram"],html.escape(str(r["holdout_id"])),
           html.escape(r["holdout_question"]),hits))
    page='''<!doctype html><html lang="ja"><meta charset="utf-8"><title>LLM_CHA Question Top-3</title>
<style>body{font:16px/1.6 system-ui,sans-serif;max-width:980px;margin:30px auto;padding:0 20px;background:#f7f8fb;color:#182238}
section{background:white;border:1px solid #d8dce5;border-radius:12px;padding:16px 22px;margin:14px 0}
small{color:#607188}code{color:#1859af}li{padding:5px 0}h1{font-size:24px}</style>
<h1>Unseen Questions → Learned Questions Top-3</h1>
<p>Only training questions are indexed. Similarity is lexical, not verified semantic relevance. Score is cosine.</p>'''+ "".join(cards)+"</html>"
    (output/"top3.html").write_text(page,encoding="utf-8")
    print(json.dumps({"train_count":len(train),"holdout_count":len(holdout),"comparisons":len(records),
       "output":str(output),"files":["top3.json","top3.csv","top3.html"]},ensure_ascii=False,indent=2))
    return records
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_corrected_v0135849.jsonl"))
    p.add_argument("--output",type=Path,default=Path("results/question_top3_v0135861"))
    a=p.parse_args()
    execute(a.source,a.output,["count","tfidf"],[2,3])
if __name__=="__main__":main()
