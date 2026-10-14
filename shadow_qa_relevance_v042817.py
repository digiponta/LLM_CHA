"""v0.4.28.17: Question–Answer Relevance Shadow Gate, offline and non-operative.

Uses explicit reviewer labels only. Never replaces Truth Gate decisions.
"""
import argparse,csv,hashlib,json
from pathlib import Path
from review_semantic_relevance_v042813 import FIELDS,summarize

def shadow(validation, comparison, reviews):
    human=summarize(validation,reviews)
    labels={(r["id"],r["turn"]):r["labels"] for r in human["manual_evaluations"]}
    source=comparison.get("records")
    if not isinstance(source,list) or len(source)!=64:raise ValueError("expected 64 comparison records")
    records=[];seen=set()
    for row in source:
        key=(row.get("id"),row.get("turn"))
        if key in seen:raise ValueError("duplicate turn")
        seen.add(key)
        relevance=labels.get(key,{}).get("final_relevant")
        gate=row.get("gate_resolution")
        if row.get("human_final_relevant") not in (None,relevance):
            raise ValueError("stale comparison human label")
        shadow_decision=("REVIEW_REJECT" if relevance is False else
                         "REVIEW_ALLOW" if relevance is True else "UNDETERMINED")
        discrepancy=("ACCEPTED_IRRELEVANT" if gate=="ACCEPT" and relevance is False else
                     "ACCEPTED_RELEVANT" if gate=="ACCEPT" and relevance is True else
                     "REJECTED_RELEVANT_REVIEW" if gate not in ("ACCEPT",None) and relevance is True else
                     "NOT_ASSESSED")
        records.append({"id":key[0],"turn":key[1],"gate_resolution":gate,
           "semantic_agreement":row.get("semantic_agreement"),
           "human_final_relevant":relevance,"shadow_relevance_decision":shadow_decision,
           "discrepancy":discrepancy,"runtime_gate_modified":False,
           "causal_attribution":"UNDETERMINED"})
    if len(seen)!=64:raise ValueError("missing records")
    return {"version":"v0.4.28.17","mode":"OFFLINE_SHADOW_LABEL_COMPARISON",
      "shadow_not_operational":True,"development_only":True,"automatic_relevance_model":False,
      "total_turns":64,
      "reviewed":sum(r["human_final_relevant"] is not None for r in records),
      "accepted_irrelevant":sum(r["discrepancy"]=="ACCEPTED_IRRELEVANT" for r in records),
      "accepted_relevant":sum(r["discrepancy"]=="ACCEPTED_RELEVANT" for r in records),
      "rejected_relevant_review":sum(r["discrepancy"]=="REJECTED_RELEVANT_REVIEW" for r in records),
      "records":records}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--validation",required=True);p.add_argument("--comparison",required=True)
    p.add_argument("--reviews",required=True);p.add_argument("--output",required=True)
    a=p.parse_args()
    try:
        files=[Path(a.validation),Path(a.comparison),Path(a.reviews)];out=Path(a.output)
        if any(not x.is_file() or x.is_symlink() for x in files):raise ValueError("invalid input")
        if out.exists() or out.is_symlink():raise ValueError("output exists")
        val=json.loads(files[0].read_text(encoding="utf-8"))
        cmp=json.loads(files[1].read_text(encoding="utf-8"))
        with files[2].open(encoding="utf-8-sig",newline="") as f:
            reader=csv.DictReader(f)
            if reader.fieldnames!=FIELDS:raise ValueError("invalid CSV fields")
            reviews=list(reader)
        result=shadow(val,cmp,reviews)
        result["source_sha256"]={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in files}
        out.parent.mkdir(parents=True,exist_ok=True)
        with out.open("x",encoding="utf-8") as f:
            json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:result[k] for k in ("total_turns","reviewed","accepted_irrelevant","accepted_relevant","rejected_relevant_review")}))
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as exc:
        p.exit(1,f"shadow analysis failed: {exc}\n")
if __name__=="__main__":main()
