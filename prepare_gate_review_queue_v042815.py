"""v0.4.28.15: read-only human review queue with Gate and probe evidence."""
import argparse, hashlib, json, re
from pathlib import Path

FOCUS_IDS = ("A04", "A05", "C05", "C07")

def build_queue(analysis, comparison):
    a=analysis.get("records")
    b=comparison.get("records")
    if not isinstance(a,list) or not isinstance(b,list) or len(a)!=64 or len(b)!=64:
        raise ValueError("requires two 64-turn reports")
    by_key={}
    for row in b:
        k=(row.get("id"),row.get("turn"))
        if k in by_key:raise ValueError("duplicate comparison turn")
        by_key[k]=row
    queue=[];seen=set()
    for row in a:
        k=(row.get("id"),row.get("turn"))
        if k in seen or k not in by_key:raise ValueError("duplicate/missing aligned turn")
        seen.add(k)
        cmp=by_key[k]
        if row.get("gate_resolution")!=cmp.get("gate_resolution"):
            raise ValueError("gate mismatch")
        if cmp.get("human_final_relevant") not in (None,True,False):
            raise ValueError("invalid human label")
        candidates=row.get("observed_candidates")
        if not isinstance(candidates,list):raise ValueError("missing candidate list")
        if row.get("candidate_alignment")=="MULTITURN_UNRESOLVED" and candidates:
            raise ValueError("unsafe multi-turn candidates")
        texts=[]
        for item in candidates:
            if not isinstance(item,dict) or not isinstance(item.get("text"),str):
                raise ValueError("invalid candidate")
            texts.append({"seed":item.get("seed"),"text":item["text"],
                          "mean_confidence":item.get("mean_confidence")})
        score=cmp.get("semantic_agreement")
        if score is not None and (not isinstance(score,(int,float)) or not 0<=score<=1):
            raise ValueError("invalid semantic score")
        human=cmp.get("human_final_relevant")
        focused=row.get("id") in FOCUS_IDS and row.get("turn")==1
        accepted=row.get("gate_resolution")=="ACCEPT"
        priority=(0 if accepted and human is False else
                  1 if focused and human is None else
                  2 if accepted and human is None else 3)
        queue.append({"id":k[0],"turn":k[1],"priority":priority,
          "priority_reason":("HUMAN_LABELED_ACCEPT_CONFLICT" if priority==0 else
                            "PRESELECTED_DEV_EXAMPLE" if priority==1 else
                            "UNREVIEWED_ACCEPT" if priority==2 else "OTHER"),
          "question":row.get("question"),"final_answer":row.get("final_answer"),
          "gate_resolution":row.get("gate_resolution"),
          "semantic_agreement":score,"human_final_relevant":human,
          "candidate_alignment":row.get("candidate_alignment"),
          "primary_text":row.get("primary_text"),"candidates":texts,
          "causal_attribution":"UNDETERMINED"})
    queue.sort(key=lambda x:(x["priority"],str(x["id"]),x["turn"]))
    return {"version":"v0.4.28.15","mode":"READ_ONLY_REVIEW_QUEUE",
            "development_only":True,"automatic_quality_judgments":False,
            "human_labeled":sum(x["human_final_relevant"] is not None for x in queue),
            "queue_length":len(queue),"focused_examples":list(FOCUS_IDS),
            "entries":queue}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--analysis",required=True)
    p.add_argument("--comparison",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    try:
        paths=[Path(args.analysis),Path(args.comparison)]
        output=Path(args.output)
        if any(not x.is_file() or x.is_symlink() for x in paths):
            raise ValueError("invalid input")
        if output.exists() or output.is_symlink():
            raise ValueError("output already exists")
        docs=[json.loads(x.read_text(encoding="utf-8")) for x in paths]
        report=build_queue(*docs)
        report["source_sha256"]={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in paths}
        output.parent.mkdir(parents=True,exist_ok=True)
        with output.open("x",encoding="utf-8") as f:
            json.dump(report,f,ensure_ascii=False,indent=2)
            f.write("\n")
        print(json.dumps({"queue_length":report["queue_length"],"human_labeled":report["human_labeled"],
                          "top_ids":[x["id"] for x in report["entries"][:4]]},ensure_ascii=False))
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as exc:
        p.exit(1,f"review queue failed: {exc}\n")
if __name__=="__main__":main()
