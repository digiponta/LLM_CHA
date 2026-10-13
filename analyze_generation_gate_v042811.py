"""v0.4.28.11: read-only generation and Gate observations (no causal claims)."""
import argparse,hashlib,json,re
from pathlib import Path
def gate_resolution(s):
    if not isinstance(s,str):return "NOT_RECORDED"
    m=re.search(r'\bresolution=([A-Z_]+)',s)
    if m:return m.group(1)
    m=re.search(r'\bgate=([A-Z_]+)',s)
    return m.group(1) if m else "NOT_RECORDED"
def analyze(capture):
    groups=capture.get("groups")
    if not isinstance(groups,list) or len(groups)!=56:raise ValueError("expected 56 groups")
    rows=[];seen=set();candidate_total=0
    for g in groups:
        ident=g.get("id")
        if ident in seen or not isinstance(ident,str):raise ValueError("duplicate/invalid group")
        seen.add(ident)
        turns=g.get("turns"); trace=g.get("stage_trace")
        if not isinstance(turns,list):raise ValueError("invalid turns")
        if not isinstance(trace,dict) or not isinstance(trace.get("generation_candidates"),list):
            raise ValueError("requires --trace-stages capture")
        events=trace["generation_candidates"]
        if any(not isinstance(e,dict) or e.get("event")!="GENERATION_CANDIDATE" or not isinstance(e.get("text"),str) for e in events):
            raise ValueError("invalid generation event")
        candidate_total+=len(events)
        # Only single-turn groups can safely associate every event with one question.
        unambiguous=len(turns)==1
        primary=next((e for e in events if e.get("seed")==0),None) if unambiguous else None
        for idx,t in enumerate(turns,1):
            if not isinstance(t,dict) or not isinstance(t.get("question"),str):raise ValueError("invalid turn")
            answer=t.get("response")
            if answer is not None and not isinstance(answer,str):raise ValueError("invalid response")
            res=gate_resolution(t.get("gate"))
            associated=events if unambiguous else []
            rows.append({"id":ident,"turn":idx,"question":t["question"],"final_answer":answer,
                "gate_resolution":res,"gate_line":t.get("gate"),
                "candidate_alignment":"SINGLE_TURN_CONFIRMED" if unambiguous else "MULTITURN_UNRESOLVED",
                "primary_text":primary["text"] if primary else None,
                "primary_matches_final":(primary["text"]==answer) if primary is not None and answer is not None else None,
                "observed_candidates":associated,
                "candidate_count":len(associated) if unambiguous else None,
                "group_candidate_count":len(events),
                "review_flags":(["ACCEPT_RELEVANCE_REVIEW"] if res=="ACCEPT" else [])+
                   (["ABSTENTION_REVIEW"] if answer=="未学習です" else []),
                "retrieval_status":"NOT_OBSERVED","causal_attribution":"UNDETERMINED"})
    if len(rows)!=64:raise ValueError("expected 64 turns")
    return {"version":"v0.4.28.11","mode":"READ_ONLY_GENERATION_GATE_CORRELATION",
       "independent_holdout":False,"causal_attribution_established":False,
       "total_turns":64,"candidate_events_total":candidate_total,
       "single_turns_aligned":sum(x["candidate_alignment"]=="SINGLE_TURN_CONFIRMED" for x in rows),
       "multiturns_unresolved":sum(x["candidate_alignment"]=="MULTITURN_UNRESOLVED" for x in rows),
       "records":rows}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--capture",required=True);p.add_argument("--output",required=True)
    a=p.parse_args()
    try:
        src=Path(a.capture);dst=Path(a.output)
        if not src.is_file() or src.is_symlink():raise ValueError("invalid input")
        if dst.exists() or dst.is_symlink():raise ValueError("output exists")
        report=analyze(json.loads(src.read_text(encoding="utf-8")))
        report["capture_sha256"]=hashlib.sha256(src.read_bytes()).hexdigest()
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:report[k] for k in ("total_turns","candidate_events_total","single_turns_aligned","multiturns_unresolved")}))
    except (OSError,ValueError,json.JSONDecodeError) as e:p.exit(1,f"correlation failed: {e}\n")
if __name__=="__main__":main()
