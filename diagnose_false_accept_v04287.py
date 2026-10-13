"""v0.4.28.7: read-only diagnostics of false-ACCEPT candidates and paraphrase instability."""
import argparse, hashlib, json
from collections import defaultdict
from pathlib import Path

PARAPHRASE_SETS={
 "gpu_definition":["B01","C01","C02","G01"],
 "llm_definition":["B05","C03","C04"],
 "sleepiness":["A04","C05","C06"],
 "reading_preference":["A09","C07","C08"],
}
def analyze(data):
    records=data.get("records")
    if not isinstance(records,list) or len(records)!=64:raise ValueError("requires 64 triage records")
    seen=set();by_id=defaultdict(list);out=[]
    for r in records:
        key=(r.get("id"),r.get("turn"))
        if key in seen:raise ValueError("duplicate record")
        seen.add(key)
        if not isinstance(r.get("question"),str) or not isinstance(r.get("flags"),list):raise ValueError("invalid record")
        ans=r.get("answer")
        if ans is not None and not isinstance(ans,str):raise ValueError("invalid answer")
        by_id[r["id"]].append(r)
        res=r.get("gate_resolution","NOT_RECORDED")
        abstain=bool(r.get("abstention"))
        flags=[]
        if res=="ACCEPT" and ans is not None and not abstain:flags.append("ACCEPT_NEEDS_RELEVANCE_REVIEW")
        if res=="ACCEPT" and (not ans or "\ufffd" in ans):flags.append("ACCEPT_OUTPUT_INTEGRITY_RISK")
        if abstain:flags.append("ABSTENTION_NEEDS_JUSTIFICATION_REVIEW")
        if ans is None:flags.append("MISSING_ANSWER")
        out.append({"id":r["id"],"turn":r["turn"],"question":r["question"],"answer":ans,
                    "gate_resolution":res,"flags":flags,
                    "manual_labels":{"answer_relevant":None,"gate_decision_appropriate":None,
                                     "fluency_ok":None,"persona_ok":None,"notes":""}})
    contrasts=[]
    for label,ids in PARAPHRASE_SETS.items():
        if any(len(by_id[x])!=1 for x in ids):raise ValueError("missing/ambiguous comparison: "+label)
        items=[by_id[x][0] for x in ids]
        states=["ABSTAIN" if x.get("abstention") else "ANSWER" if x.get("answer") is not None else "MISSING" for x in items]
        contrasts.append({"set":label,"ids":ids,"questions":[x["question"] for x in items],
                          "answer_statuses":states,"mixed_abstention":"ABSTAIN" in states and "ANSWER" in states,
                          "resolution_types":sorted({x.get("gate_resolution","NOT_RECORDED") for x in items}),
                          "manual_semantic_equivalence":None,
                          "notes":"Development comparison; phrase equivalence not assumed."})
    return {"version":"v0.4.28.7","evaluation":"DEVELOPMENT_ONLY_DIAGNOSTIC",
            "human_quality_evaluated":False,"truth_gate_modified":False,
            "total_turns":len(out),"accept_count":sum(x["gate_resolution"]=="ACCEPT" for x in out),
            "accept_relevance_review_count":sum("ACCEPT_NEEDS_RELEVANCE_REVIEW" in x["flags"] for x in out),
            "abstention_review_count":sum("ABSTENTION_NEEDS_JUSTIFICATION_REVIEW" in x["flags"] for x in out),
            "paraphrase_sets":contrasts,
            "paraphrase_sets_with_mixed_abstention":sum(x["mixed_abstention"] for x in contrasts),
            "records":out,"interpretation":"Review flags are not proven failures or error rates."}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True);p.add_argument("--output",required=True)
    a=p.parse_args()
    try:
        src,dst=Path(a.input),Path(a.output)
        if not src.is_file() or src.is_symlink():raise ValueError("missing/unsafe input")
        if dst.exists() or dst.is_symlink():raise ValueError("output already exists")
        result=analyze(json.loads(src.read_text(encoding="utf-8")))
        result["source_sha256"]=hashlib.sha256(src.read_bytes()).hexdigest()
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        keys=("total_turns","accept_count","accept_relevance_review_count","abstention_review_count","paraphrase_sets_with_mixed_abstention")
        print(json.dumps({k:result[k] for k in keys},ensure_ascii=False))
    except (ValueError,OSError,json.JSONDecodeError) as e:p.exit(1,f"diagnostic failed: {e}\n")
if __name__=="__main__":main()
