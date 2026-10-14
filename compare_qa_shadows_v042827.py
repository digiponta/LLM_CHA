"""v0.4.28.27: read-only cross-tab of existing lexical and function shadows.

Never combines diagnostic signals into a runtime reject rule.
"""
import argparse,hashlib,json
from pathlib import Path
from qa_relevance_shadow_v042825 import triage
from qa_function_shadow_v042826 import report as function_report
from analyze_chatgpt_qa_gate_v042824 import analyze

def compare(validation,labels,comparison):
    audit=analyze(validation,labels,comparison)
    lex=triage(audit)
    fun=function_report(validation,labels,comparison)
    l={(r["id"],r["turn"]):r for r in lex["records"]}
    f={(r["id"],r["turn"]):r for r in fun["records"]}
    if len(l)!=64 or len(f)!=64 or set(l)!=set(f):raise ValueError("shadow mismatch")
    rows=[];matrix={}
    for key in sorted(l):
        a,b=l[key],f[key]
        if a["chatgpt_relevant"] is not b["chatgpt_relevant"] or a["original_gate_resolution"]!=b["gate_resolution"]:
            raise ValueError("shadow provenance mismatch")
        pair=(a["shadow_decision"],b["shadow_decision"])
        name=pair[0]+" | "+pair[1]
        matrix[name]=matrix.get(name,0)+1
        rows.append({"id":key[0],"turn":key[1],"lexical_decision":pair[0],
          "function_decision":pair[1],"chatgpt_relevant":a["chatgpt_relevant"],
          "gate_resolution":a["original_gate_resolution"],
          "lexical_overlap":a["lexical_overlap"],"semantic_agreement":a["semantic_agreement"],
          "function_reason":b["reason_code"]})
    return {"version":"v0.4.28.27","mode":"OFFLINE_TWO_SHADOW_COMPARISON",
      "development_only":True,"human_ground_truth":False,"independent_holdout":False,
      "runtime_modified":False,"combined_reject_rule":False,"threshold_fitted":False,
      "total":len(rows),"matrix":dict(sorted(matrix.items())),
      "lexical_review":sum(r["lexical_decision"]=="REVIEW_CANDIDATE" for r in rows),
      "function_review":sum(r["function_decision"]=="REVIEW_CANDIDATE" for r in rows),
      "both_review":sum(r["lexical_decision"]=="REVIEW_CANDIDATE" and r["function_decision"]=="REVIEW_CANDIDATE" for r in rows),
      "either_review_descriptive":sum(r["lexical_decision"]=="REVIEW_CANDIDATE" or r["function_decision"]=="REVIEW_CANDIDATE" for r in rows),
      "either_review_positive":sum((r["lexical_decision"]=="REVIEW_CANDIDATE" or r["function_decision"]=="REVIEW_CANDIDATE") and r["chatgpt_relevant"] is True for r in rows),
      "either_review_negative":sum((r["lexical_decision"]=="REVIEW_CANDIDATE" or r["function_decision"]=="REVIEW_CANDIDATE") and r["chatgpt_relevant"] is False for r in rows),
      "accepted_negative_neither_review":sum(r["gate_resolution"]=="ACCEPT" and r["chatgpt_relevant"] is False and r["lexical_decision"]!="REVIEW_CANDIDATE" and r["function_decision"]!="REVIEW_CANDIDATE" for r in rows),
      "records":rows}

def main():
    p=argparse.ArgumentParser()
    for field in ("validation","labels","comparison","output"):p.add_argument("--"+field,required=True)
    a=p.parse_args()
    try:
        paths=[Path(a.validation),Path(a.labels),Path(a.comparison)]
        dst=Path(a.output)
        if any(not x.is_file() or x.is_symlink() for x in paths) or dst.exists() or dst.is_symlink():
            raise ValueError("invalid input/output")
        payload=[json.loads(x.read_text(encoding="utf-8-sig")) for x in paths]
        result=compare(*payload)
        result["sha256"]={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in paths}
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write("\n")
        print(json.dumps({k:result[k] for k in ("total","lexical_review","function_review","both_review","either_review_descriptive","either_review_positive","either_review_negative","accepted_negative_neither_review")}))
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:p.exit(1,f"shadow comparison failed: {exc}\n")
if __name__=="__main__":main()
