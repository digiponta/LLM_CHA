"""v0.4.28.14: evidence-limited Gate semantic agreement vs human relevance."""
import argparse,csv,hashlib,json,re
from pathlib import Path
from review_semantic_relevance_v042813 import FIELDS,summarize

def compare(validation,capture,reviews):
    human=summarize(validation,reviews)
    labeled={(r["id"],int(r["turn"])):r["labels"] for r in human["manual_evaluations"]}
    gates={}
    groups=capture.get("groups")
    if not isinstance(groups,list) or len(groups)!=56:raise ValueError("expected 56 captured groups")
    for group in groups:
        for n,turn in enumerate(group.get("turns",[]),1):
            key=(group["id"],n)
            if key in gates:raise ValueError("duplicate capture turn")
            line=turn.get("gate")
            match=re.search(r"(?<![\w])sem_agreement=([^,\]\s]+)",line) if isinstance(line,str) else None
            score=None
            if match:
                try:
                    value=float(match.group(1))
                    if 0<=value<=1:score=value
                except ValueError:pass
            gates[key]={"question":turn.get("question"),"answer":turn.get("response"),"score":score}
    rows=[];used=set()
    for r in validation["records"]:
        key=(r["id"],r["turn"])
        if key not in gates or key in used:raise ValueError("missing/duplicate alignment")
        used.add(key)
        g=gates[key]
        if g["question"]!=r["question"] or g["answer"]!=r["final_answer"]:
            raise ValueError("source mismatch "+str(key))
        labels=labeled.get(key,{})
        relevance=labels.get("final_relevant")
        score=g["score"]
        rows.append({"id":key[0],"turn":key[1],"gate_resolution":r.get("gate_resolution"),
          "semantic_agreement":score,"human_final_relevant":relevance,
          "assessment":"LABELED_ACCEPT_RELEVANCE_CONFLICT" if relevance is False and r.get("gate_resolution")=="ACCEPT" else
             "LABELED_ACCEPT_RELEVANT" if relevance is True and r.get("gate_resolution")=="ACCEPT" else "NOT_ASSESSED",
          "root_cause":"UNDETERMINED"})
    if len(rows)!=64 or len(gates)!=64:raise ValueError("requires 64 aligned turns")
    labeled_with_score=[r for r in rows if r["human_final_relevant"] is not None and r["semantic_agreement"] is not None]
    return {"version":"v0.4.28.14","development_only":True,"causal_attribution_established":False,
      "total_turns":64,"gate_semantic_scores_observed":sum(r["semantic_agreement"] is not None for r in rows),
      "human_relevance_labeled":sum(r["human_final_relevant"] is not None for r in rows),
      "paired_score_and_human_relevance":len(labeled_with_score),
      "labeled_accept_relevance_conflicts":sum(r["assessment"]=="LABELED_ACCEPT_RELEVANCE_CONFLICT" for r in rows),
      "records":rows}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--validation",required=True);p.add_argument("--capture",required=True)
    p.add_argument("--reviews",required=True);p.add_argument("--output",required=True)
    a=p.parse_args()
    try:
        inputs=[Path(a.validation),Path(a.capture),Path(a.reviews)];dest=Path(a.output)
        if any(not s.is_file() or s.is_symlink() for s in inputs):raise ValueError("invalid source")
        if dest.exists() or dest.is_symlink():raise ValueError("output exists")
        v=json.loads(inputs[0].read_text(encoding="utf-8"))
        c=json.loads(inputs[1].read_text(encoding="utf-8"))
        with inputs[2].open(encoding="utf-8-sig",newline="") as f:
            reader=csv.DictReader(f)
            if reader.fieldnames!=FIELDS:raise ValueError("unexpected review headers")
            review_rows=list(reader)
        result=compare(v,c,review_rows)
        result["source_sha256"]={s.name:hashlib.sha256(s.read_bytes()).hexdigest() for s in inputs}
        dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:result[k] for k in ("total_turns","gate_semantic_scores_observed","human_relevance_labeled","paired_score_and_human_relevance","labeled_accept_relevance_conflicts")}))
    except (OSError,ValueError,json.JSONDecodeError) as e:p.exit(1,f"comparison failed: {e}\n")
if __name__=="__main__":main()
