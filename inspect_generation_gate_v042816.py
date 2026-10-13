"""v0.4.28.16: evidence packet separating generation and Gate questions.

This tool does not infer primary answer relevance, Gate causality, or retrieval.
"""
import argparse,hashlib,json
from pathlib import Path

FOCUS=("A04","A05","C05","C07")

def build_packet(queue, focus=FOCUS):
    entries=queue.get("entries")
    if not isinstance(entries,list) or len(entries)!=64:
        raise ValueError("expected 64-entry v042815 review queue")
    by_key={}
    for e in entries:
        key=(e.get("id"),e.get("turn"))
        if key in by_key:raise ValueError("duplicate queue entry")
        by_key[key]=e
    selected=[]
    for ident in focus:
        key=(ident,1)
        if key not in by_key:raise ValueError("missing focused turn "+ident)
        e=by_key[key]
        if not isinstance(e.get("question"),str):raise ValueError("invalid question")
        if e.get("final_answer") is not None and not isinstance(e["final_answer"],str):
            raise ValueError("invalid final answer")
        if e.get("candidate_alignment")=="MULTITURN_UNRESOLVED" and e.get("candidates"):
            raise ValueError("ambiguous candidate attribution")
        candidates=e.get("candidates")
        if not isinstance(candidates,list) or any(not isinstance(c,dict) or not isinstance(c.get("text"),str) for c in candidates):
            raise ValueError("invalid candidates")
        label=e.get("human_final_relevant")
        if label is not None and type(label) is not bool:raise ValueError("invalid label")
        accepted=e.get("gate_resolution")=="ACCEPT"
        selected.append({
          "id":ident,"turn":1,"question":e["question"],"final_answer":e.get("final_answer"),
          "gate_resolution":e.get("gate_resolution"),"semantic_agreement":e.get("semantic_agreement"),
          "candidate_alignment":e.get("candidate_alignment"),"primary_text":e.get("primary_text"),
          "candidates":candidates,"human_final_relevant":label,
          "generation_relevance_status":"NOT_LABELED",
          "gate_acceptance_status":("HUMAN_LABELED_IRRELEVANT_ACCEPT" if accepted and label is False else
             "HUMAN_LABELED_RELEVANT_ACCEPT" if accepted and label is True else "NOT_EVALUATED"),
          "retrieval_status":"NOT_OBSERVED","causal_attribution":"UNDETERMINED",
          "review_questions":[
             "Is the observed primary candidate relevant to the input question?",
             "Are probe outputs mutually semantically equivalent and relevant to the question?",
             "Does the final answer meet the input intent?",
             "Was the Gate decision appropriate given the evidence?"
          ]
        })
    return {"version":"v0.4.28.16","mode":"FOCUSED_GENERATION_GATE_REVIEW_PACKET",
       "development_only":True,"causal_attribution_established":False,
       "focused_turns":len(selected),
       "human_final_relevance_labeled":sum(x["human_final_relevant"] is not None for x in selected),
       "cases":selected}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--queue",required=True);p.add_argument("--output",required=True)
    a=p.parse_args()
    try:
        src,dst=Path(a.queue),Path(a.output)
        if not src.is_file() or src.is_symlink():raise ValueError("invalid input")
        if dst.exists() or dst.is_symlink():raise ValueError("output exists")
        report=build_packet(json.loads(src.read_text(encoding="utf-8")))
        report["queue_sha256"]=hashlib.sha256(src.read_bytes()).hexdigest()
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:
            json.dump(report,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({"focused_turns":report["focused_turns"],
            "human_final_relevance_labeled":report["human_final_relevance_labeled"],
            "ids":[x["id"] for x in report["cases"]]},ensure_ascii=False))
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as e:p.exit(1,f"review packet failed: {e}\n")
if __name__=="__main__":main()
