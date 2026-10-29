"""v0.13.58.69: Answer Reuse reranking experiment on reviewed Top-10.

Uses lexical evidence, conservative safety/capability checks, and existing
semantic scores. Not a learned classifier; no independent generalization claim.
No per-question lookup rules or label leakage in the scoring function.
"""
import argparse,csv,json,re,unicodedata
from pathlib import Path
from collections import defaultdict

def clean(s):
    return re.sub(r"\s+","",unicodedata.normalize("NFKC",str(s)).lower())

def char_ngrams(s,n=2):
    s=clean(s)
    return {s[i:i+n] for i in range(max(0,len(s)-n+1))}

def overlap(a,b):
    x,y=char_ngrams(a),char_ngrams(b)
    return len(x&y)/len(x|y) if x and y else 0.

def signals(query,question,answer):
    q,a=clean(query),clean(answer)
    # Explicit action and task requirements are impossible to fulfill via a
    # generic stored daily-conversation answer.
    facts=bool(re.search(r"為替|レート|最新|観測結果|天気|予報|犬種|この写真|連立方程式|途中式|薬の量|用量",q))
    specificity=bool(re.search(r"教えて|いくら|解いて|決めて|示して",q))
    unsupported=facts and specificity
    # Detect polarity/turn-control conflicts, including '新しい話題に変えたい',
    # which earlier intent rules sometimes missed.
    change=bool(re.search(r"別の話|新しい話題|話題を変|話を変|別のこと|ほかの話",q))
    continue_reply=bool(re.search(r"続き|話に戻|さっきの話",clean(question)))
    return {"question_overlap":round(overlap(q,question),6),
            "answer_overlap":round(overlap(q,a),6),
            "unsupported_specific_request":unsupported,
            "change_vs_continue":change and continue_reply}

def rank_candidates(query,candidates,weight_question=.08,weight_answer=.02,conflict_penalty=.12,unsupported_penalty=.25):
    ranked=[]
    for h in candidates:
        z=signals(query,h["candidate_question"],h["candidate_answer"])
        base=float(h["adjusted_score"])
        score=base+weight_question*z["question_overlap"]+weight_answer*z["answer_overlap"]
        if z["change_vs_continue"]:score-=conflict_penalty
        if z["unsupported_specific_request"]:score-=unsupported_penalty
        ranked.append({**h,**z,"base_adjusted_score":base,"reuse_score":round(score,6)})
    ranked.sort(key=lambda h:(-h["reuse_score"],h["candidate_id"]))
    for i,h in enumerate(ranked):h["new_rank"]=i+1
    return ranked

def read_reviews(path):
    with path.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
    groups=defaultdict(list)
    for r in rows:
        if r.get("review_status")!="APPROVED" or r.get("answer_reusable") not in ("YES","NO"):
            raise ValueError(f'{r.get("query_id")}: incomplete review')
        groups[r["query_id"]].append(r)
    if not groups:raise ValueError("no reviews")
    for q,items in groups.items():
        if len(items)!=10 or sorted(int(x["rank"]) for x in items)!=list(range(1,11)):
            raise ValueError(f"{q}: expected 10 ranked candidates")
        if len({x["candidate_id"] for x in items})!=10:raise ValueError("duplicate candidates")
    return groups

def score(groups):
    results=[]
    for q,items in groups.items():
        old=sorted(items,key=lambda x:int(x["rank"]))
        new=rank_candidates(old[0]["query"],old)
        old_ok=old[0]["answer_reusable"]=="YES"
        new_ok=new[0]["answer_reusable"]=="YES"
        results.append({"query_id":q,"query":old[0]["query"],"original_top1":old[0]["candidate_id"],
          "reranked_top1":new[0]["candidate_id"],"original_ok":old_ok,"reranked_ok":new_ok,
          "top10_reusable":any(x["answer_reusable"]=="YES" for x in old),
          "changed":old[0]["candidate_id"]!=new[0]["candidate_id"],"candidates":new})
    return {"query_count":len(results),
      "original_top1_reusable":sum(x["original_ok"] for x in results),
      "reranked_top1_reusable":sum(x["reranked_ok"] for x in results),
      "changed_count":sum(x["changed"] for x in results),
      "top10_has_reusable":sum(x["top10_reusable"] for x in results),
      "results":results}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--review",type=Path,default=Path("data/answer_reuse_review_v0135867.csv"))
    p.add_argument("--output",type=Path,default=Path("results/answer_reuse_rerank_v0135869.json"))
    args=p.parse_args()
    groups=read_reviews(args.review)
    report=score(groups)
    report.update({"version":"v0.13.58.69","evaluation":"EXPLORATORY_REUSED_DEV",
       "label_used_in_ranking":False,"independent_evaluation":False,
       "warning":"Rules informed by viewed data; no independent test. Top10 absence is not whole-library unknown."})
    if args.output.exists():raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for x in report["results"]:
        print(f'{x["query_id"]} old={x["original_top1"]} ({x["original_ok"]}) new={x["reranked_top1"]} ({x["reranked_ok"]})')
    print("summary:",json.dumps({k:v for k,v in report.items() if k not in ("results","warning")},ensure_ascii=False))
    print("report:",args.output)
if __name__=="__main__":main()
