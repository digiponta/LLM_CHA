"""v0.4.28.8 evidence-limited, read-only pipeline attribution."""
import argparse, hashlib, json, re
from pathlib import Path

def diagnose(triage, capture=None):
    records=triage.get("records")
    if not isinstance(records,list) or len(records)!=64:
        raise ValueError("expected 64 quality-triage records")
    raw={}
    if capture is not None:
        groups=capture.get("groups")
        if not isinstance(groups,list):raise ValueError("invalid capture")
        for g in groups:
            if not isinstance(g.get("turns"),list):raise ValueError("invalid capture group")
            for pos,t in enumerate(g["turns"],1):
                key=(g.get("id"),pos)
                if key in raw:raise ValueError("duplicate capture turn")
                raw[key]=t
    output=[];seen=set()
    for r in records:
        key=(r.get("id"),r.get("turn"))
        if key in seen:raise ValueError("duplicate triage turn")
        seen.add(key)
        if not isinstance(r.get("question"),str):raise ValueError("missing question")
        ans=r.get("answer")
        if ans is not None and not isinstance(ans,str):raise ValueError("invalid answer")
        t=raw.get(key)
        if capture is not None:
            if t is None or t.get("question")!=r["question"] or t.get("response")!=ans:
                raise ValueError("capture/triage mismatch: "+str(key))
        gate=r.get("gate_resolution","NOT_RECORDED")
        gate_log=t.get("gate") if t else None
        evidence=[]
        if gate_log:
            reason=re.search(r"\breason=([^\]\n]+)",gate_log)
            if reason:evidence.append({"source":"gate_log","type":"GATE_REASON","value":reason.group(1).strip()})
        if ans is not None:evidence.append({"source":"triage","type":"FINAL_ANSWER_OBSERVED","value":True})
        if gate in ("ACCEPT","GATE_REVIEW","UNKNOWN_KNOWLEDGE","KNOWN"):
            evidence.append({"source":"triage","type":"GATE_RESOLUTION","value":gate})
        # Retrieval hits and raw model output are not reliably exposed by this format.
        # A recorded gate reason describes runtime behavior, not proven root cause.
        output.append({"id":key[0],"turn":key[1],"question":r["question"],"answer":ans,
          "gate_resolution":gate,"observations":evidence,
          "retrieval_attribution":"UNDETERMINED",
          "generation_attribution":"UNDETERMINED",
          "gate_attribution":"UNDETERMINED",
          "review_priority":"HIGH" if gate=="ACCEPT" and ans not in (None,"","未学習です") else "NORMAL",
          "human_review":{"relevant":None,"retrieval_evidence":None,"generation_evidence":None,"gate_evidence":None,"notes":""}})
    return {"version":"v0.4.28.8","mode":"READ_ONLY_EVIDENCE_DIAGNOSTIC",
      "independent_holdout":False,"causal_attribution_established":False,
      "total_turns":len(output),"with_gate_log":sum(any(e["source"]=="gate_log" for e in x["observations"]) for x in output),
      "unattributed_turns":len(output),"records":output,
      "required_next_instrumentation":["retrieval_candidate_ids_and_scores","raw_generation_before_gate","gate_decision_inputs_and_thresholds"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--triage",required=True);p.add_argument("--capture")
    p.add_argument("--output",required=True);a=p.parse_args()
    try:
        src=Path(a.triage);dst=Path(a.output)
        if not src.is_file() or src.is_symlink():raise ValueError("missing/unsafe triage")
        if dst.exists() or dst.is_symlink():raise ValueError("output exists")
        capture=None
        if a.capture:
            cp=Path(a.capture)
            if not cp.is_file() or cp.is_symlink():raise ValueError("missing/unsafe capture")
            capture=json.loads(cp.read_text(encoding="utf-8"))
        result=diagnose(json.loads(src.read_text(encoding="utf-8")),capture)
        result["triage_sha256"]=hashlib.sha256(src.read_bytes()).hexdigest()
        if a.capture:result["capture_sha256"]=hashlib.sha256(cp.read_bytes()).hexdigest()
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:result[k] for k in ("total_turns","with_gate_log","unattributed_turns")}))
    except (ValueError,OSError,json.JSONDecodeError) as e:p.exit(1,f"attribution diagnostic failed: {e}\n")
if __name__=="__main__":main()
