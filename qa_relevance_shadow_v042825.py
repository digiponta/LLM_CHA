"""v0.4.28.25: independent lexical QA shadow triage, NEVER runtime gating.

A zero bigram overlap is a review signal, not an irrelevant-answer verdict.
ChatGPT provisional labels are used ONLY after decisions are fixed.
"""
import argparse,hashlib,json
from pathlib import Path
from analyze_chatgpt_qa_gate_v042824 import analyze

def triage(audit):
    rows=audit.get("records")
    if not isinstance(rows,list) or len(rows)!=64:raise ValueError("64 aligned audit records required")
    seen=set();output=[]
    for r in rows:
        key=(r.get("id"),r.get("turn"))
        if key in seen:raise ValueError("duplicate turn")
        seen.add(key)
        overlap=r.get("lexical_overlap")
        if overlap is not None and (isinstance(overlap,bool) or not isinstance(overlap,(int,float)) or not 0<=overlap<=1):
            raise ValueError("invalid lexical_overlap")
        # Only question/answer-derived lexical observation; no ChatGPT labels or Gate scores influence decision.
        decision="NO_SIGNAL" if overlap is None else "REVIEW_CANDIDATE" if overlap==0 else "NO_FLAG"
        output.append({"id":key[0],"turn":key[1],"shadow_decision":decision,
          "chatgpt_relevant":r["chatgpt_relevant"],
          "original_gate_resolution":r["gate_resolution"],
          "lexical_overlap":overlap,"semantic_agreement":r["semantic_agreement"]})
    eligible=[r for r in output if r["chatgpt_relevant"] is not None]
    flagged=[r for r in eligible if r["shadow_decision"]=="REVIEW_CANDIDATE"]
    return {"version":"v0.4.28.25","mode":"NONOPERATIVE_LEXICAL_REVIEW_SHADOW",
      "metric":"question_answer_character_bigram_recall",
      "rule":"zero_overlap_flags_for_review_only",
      "decision_uses_labels":False,"decision_uses_gate":False,
      "truth_gate_modified":False,"human_ground_truth":False,
      "independent_holdout":False,"threshold_fitted":False,
      "total_turns":len(output),"flagged_for_review":sum(r["shadow_decision"]=="REVIEW_CANDIDATE" for r in output),
      "flagged_provisional_negative":sum(r["chatgpt_relevant"] is False for r in flagged),
      "flagged_provisional_positive":sum(r["chatgpt_relevant"] is True for r in flagged),
      "flagged_originally_accepted":sum(r["shadow_decision"]=="REVIEW_CANDIDATE" and r["original_gate_resolution"]=="ACCEPT" for r in output),
      "flagged_accepted_provisional_negative":sum(r["shadow_decision"]=="REVIEW_CANDIDATE" and r["original_gate_resolution"]=="ACCEPT" and r["chatgpt_relevant"] is False for r in output),
      "records":output}

def main():
    p=argparse.ArgumentParser()
    for n in ("validation","labels","comparison","output"):p.add_argument("--"+n,required=True)
    a=p.parse_args()
    try:
        paths=[Path(a.validation),Path(a.labels),Path(a.comparison)]
        dst=Path(a.output)
        if any(not f.is_file() or f.is_symlink() for f in paths) or dst.exists() or dst.is_symlink():raise ValueError("invalid input/output")
        v,l,c=[json.loads(f.read_text(encoding="utf-8-sig")) for f in paths]
        report=triage(analyze(v,l,c))
        report["sha256"]={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in paths}
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:report[k] for k in ("total_turns","flagged_for_review","flagged_provisional_negative","flagged_provisional_positive","flagged_accepted_provisional_negative")}))
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:p.exit(1,f"shadow failed: {e}\n")
if __name__=="__main__":main()
