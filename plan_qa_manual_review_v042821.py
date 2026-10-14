"""v0.4.28.21: read-only manual review progress and batches."""
import argparse,csv,json,hashlib
from pathlib import Path
from review_semantic_relevance_v042813 import FIELDS,summarize

FOCUS={"A04","A05","C05","C07"}

def plan(data, reviews, batch_size=8):
    if not isinstance(batch_size,int) or not 1<=batch_size<=64:
        raise ValueError("batch size must be 1..64")
    report=summarize(data,reviews)
    if len(reviews)!=64:raise ValueError("requires all 64 worksheet rows")
    entries=[]
    seen=set()
    for r in reviews:
        key=(r["id"],r["turn"])
        if key in seen:raise ValueError("duplicate review key")
        seen.add(key)
        val=r["final_relevant"].strip().lower()
        if val not in ("true","false",""):raise ValueError("invalid final_relevant")
        entries.append({"id":key[0],"turn":int(key[1]),"question":r["question"],
          "final_answer":r["final_answer"],"final_relevant":None if not val else val=="true",
          "focus_example":key[0] in FOCUS})
    todo=[r for r in entries if r["final_relevant"] is None]
    todo.sort(key=lambda r:(not r["focus_example"],r["id"],r["turn"]))
    batches=[{"batch":i//batch_size+1,"items":todo[i:i+batch_size]} for i in range(0,len(todo),batch_size)]
    return {"version":"v0.4.28.21","mode":"MANUAL_REVIEW_PLANNING",
       "development_only":True,"automatic_labels_added":0,"truth_gate_modified":False,
       "total_turns":64,"final_relevant_labeled":64-len(todo),
       "positive":sum(r["final_relevant"] is True for r in entries),
       "negative":sum(r["final_relevant"] is False for r in entries),
       "unlabeled":len(todo),"batches":batches,
       "source_reviewed_any_field":report["reviewed_turns"],
       "accuracy_estimate":"UNAVAILABLE","threshold_estimated":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--validation",required=True);p.add_argument("--reviews",required=True)
    p.add_argument("--output",required=True);p.add_argument("--batch-size",type=int,default=8)
    a=p.parse_args()
    try:
        source,review_path,dst=Path(a.validation),Path(a.reviews),Path(a.output)
        if any(not path.is_file() or path.is_symlink() for path in (source,review_path)):
            raise ValueError("invalid source")
        if dst.exists() or dst.is_symlink():raise ValueError("output exists")
        data=json.loads(source.read_text(encoding="utf-8"))
        with review_path.open(encoding="utf-8-sig",newline="") as f:
            reader=csv.DictReader(f)
            if reader.fieldnames!=FIELDS:raise ValueError("invalid CSV header")
            rows=list(reader)
        result=plan(data,rows,a.batch_size)
        result["sha256"]={path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in (source,review_path)}
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:
            json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:result[k] for k in ("total_turns","final_relevant_labeled","positive","negative","unlabeled")}))
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as e:
        p.exit(1,f"review planning failed: {e}\n")
if __name__=="__main__":main()
