"""v0.13.58.63 Japanese semantic retrieval baseline (train-only index).
Ruri symmetric meaning mode (empty prefixes) and asymmetric retrieval mode
(検索クエリ: / 検索文書: ) are compared, not mixed. Never interpret cosine
as calibrated semantic relevance or probability. No LLM checkpoint changes.
"""
import argparse,csv,hashlib,html,json
from pathlib import Path
from train_daily_generation_v0135847 import dataset
from retrieve_question_top3_v0135861 import retrieve,norm

MODEL="cl-nagoya/ruri-v3-30m"
MODES={"semantic":("",""),"retrieval":("検索クエリ: ","検索文書: ")}
def topk(vectors,index,rows,k=3):
    import numpy as np
    values=np.asarray(vectors)@np.asarray(index).T
    output=[]
    for line in values:
        order=sorted(range(len(rows)),key=lambda i:(-float(line[i]),str(rows[i]["id"])))[:k]
        output.append([{"rank":j+1,"id":rows[i]["id"],"question":rows[i]["user"],
                        "answer":rows[i]["assistant"],"score":round(float(line[i]),6)}
                       for j,i in enumerate(order)])
    return output
def render(results,output):
    pieces=[]
    for case in results:
        items="".join("<li><b>#%s</b> <code>%.4f</code> %s <small>%s</small></li>"%
                      (hit["rank"],hit["score"],html.escape(hit["question"]),html.escape(str(hit["id"])))
                      for hit in case["top3"])
        pieces.append("<section><small>%s / %s</small><h3>%s</h3><ol>%s</ol></section>"%
                      (html.escape(case["method"]),html.escape(str(case["holdout_id"])),
                       html.escape(case["holdout_question"]),items))
    page='''<!doctype html><html lang="ja"><meta charset="utf-8"><title>LLM_CHA Retrieval Compare</title>
<style>body{font:16px/1.65 system-ui,sans-serif;max-width:1000px;margin:30px auto;padding:0 20px;background:#f6f8fc;color:#172136}
section{background:#fff;border:1px solid #dce1e9;border-radius:12px;padding:16px 24px;margin:12px 0}
small{color:#627187}code{color:#185bb5}li{padding:5px 0}</style><h1>Holdout → Learned Question Top-3</h1>
<p>Lexical vs Japanese embeddings. Scores are not confidence probabilities. No verified gold relevance labels yet.</p>'''+ "".join(pieces)+"</html>"
    (output/"comparison.html").write_text(page,encoding="utf-8")
def run(a):
    if a.output.exists():raise FileExistsError(a.output)
    train,held,protected=dataset(a.source)
    if len(train)!=56 or len(held)!=8:raise ValueError("requires 56 train and 8 holdout")
    ids={q["id"] for q in train}
    if len(ids)!=56 or ids.intersection(q["id"] for q in held):raise ValueError("ID leakage")
    if {norm(q["user"]) for q in train}.intersection(norm(q["user"]) for q in held):
        raise ValueError("text leakage")
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer
    device="cuda" if torch.cuda.is_available() and not a.cpu else "cpu"
    embed=SentenceTransformer(MODEL,device=device,trust_remote_code=False)
    results=[]
    for mode,(qp,dp) in MODES.items():
        indexed=embed.encode([dp+r["user"] for r in train],normalize_embeddings=True,
                             batch_size=a.batch_size,show_progress_bar=False)
        queries=embed.encode([qp+r["user"] for r in held],normalize_embeddings=True,
                             batch_size=a.batch_size,show_progress_bar=False)
        for q,top in zip(held,topk(queries,indexed,train)):
            results.append({"method":"ruri-"+mode,"holdout_id":q["id"],
                            "holdout_question":q["user"],"top3":top})
    for mode in ("count","tfidf"):
        for q in held:
            results.append({"method":mode+"-char2","holdout_id":q["id"],
                            "holdout_question":q["user"],"top3":retrieve(train,q["user"],2,mode)})
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"comparison.json").write_text(json.dumps({
        "version":"v0.13.58.63","model":MODEL,"device":device,
        "train_count":len(train),"holdout_count":len(held),
        "gold_labels_available":False,"independent_final_test":False,
        "caution":"Cosine is not semantic-relevance probability; lexical and neural scores cannot be compared directly.",
        "results":results},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (a.output/"comparison.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=["method","holdout_id","holdout_question","rank",
                                        "score","train_id","train_question","train_answer","relevance_review"])
        w.writeheader()
        for record in results:
            for hit in record["top3"]:
                w.writerow({"method":record["method"],"holdout_id":record["holdout_id"],
                    "holdout_question":record["holdout_question"],"rank":hit["rank"],
                    "score":hit["score"],"train_id":hit["id"],
                    "train_question":hit["question"],"train_answer":hit["answer"],
                    "relevance_review":""})
    render(results,a.output)
    print(json.dumps({"status":"COMPLETE_UNREVIEWED","train":len(train),"holdout":len(held),
        "mode_count":4,"top3_rows":len(results)*3,"device":device,"output":str(a.output)},ensure_ascii=False))
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/daily_sft_corrected_v0135849.jsonl"))
    p.add_argument("--output",type=Path,default=Path("results/semantic_top3_v0135863"))
    p.add_argument("--batch-size",type=int,default=16)
    p.add_argument("--cpu",action="store_true")
    run(p.parse_args())
if __name__=="__main__":main()
