"""RSE gate benchmark. Human labels must be independently reviewed.

Labels: suitable=true means a source answer MAY be reused by AI without
inventing personal experience; false means reject. "MANUAL_REVIEW_REQUIRED"
is abstention, not acceptance. Never auto-promote.
"""
import argparse,json,collections
from pathlib import Path
from rse_selection_gate_v013588304 import gate

def measure(cases):
    rows=[];conf=collections.Counter()
    for c in cases:
        if c.get("suitable") not in (True,False):
            raise ValueError("Every benchmark case requires boolean suitable label")
        g=gate(c["query"],c["source_question"],c["source_answer"])
        decision=g["status"]
        label=c["suitable"]
        if decision=="REJECT":
            conf["false_reject" if label else "true_reject"]+=1
        elif decision=="MANUAL_REVIEW_REQUIRED":
            conf["review_positive" if label else "review_negative"]+=1
        else:
            raise ValueError("Unknown gate decision: "+str(decision))
        rows.append({"id":c["id"],"suitable":label,"decision":decision,"reasons":g["reasons"]})
    positive=conf["false_reject"]+conf["review_positive"]
    negative=conf["true_reject"]+conf["review_negative"]
    return {"status":"EVALUATION_ONLY","cases":len(rows),
            "human_labels_independently_verified":False,
            "no_auto_accept_path":True,
            "true_reject":conf["true_reject"],"false_reject":conf["false_reject"],
            "review_positive":conf["review_positive"],"review_negative":conf["review_negative"],
            "rejection_recall_on_negative":conf["true_reject"]/negative if negative else None,
            "false_rejection_rate_on_positive":conf["false_reject"]/positive if positive else None,
            "candidate_review_coverage":(conf["review_positive"]+conf["review_negative"])/len(rows) if rows else None,
            "rows":rows}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--cases",default="data/rse_gate_benchmark_v013588306.json")
    p.add_argument("--output",default="results/rse_gate_benchmark_v013588306.json")
    a=p.parse_args()
    data=json.loads(Path(a.cases).read_text(encoding="utf-8-sig"))
    result=measure(data["cases"])
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
