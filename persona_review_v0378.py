"""v0.3.7.8: inspect and adjudicate raw-corpus means candidates.

No automatic labels. Use separate human-reviewed verdicts before reporting
precision. A fixture-based query evaluation is not a model-quality score.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
from persona_means_audit_v0376 import extract
from persona_normalized_means_v0377 import lookup

VERDICTS=("CORRECT","AMBIGUOUS","INCORRECT")
def candidate_id(row):
    key=f'{row["source"]}|{row["line"]}|{row["segment"]}|{row["original"]}'
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]

def review_rows(source):
    result=[]
    for row in extract(source):
        result.append({"id":candidate_id(row),"line":row["line"],"segment":row["segment"],
                       "original":row["original"],"subject":row["subject"],
                       "means":row["means"],"predicate":row["predicate"],
                       "marker":row["marker"],"verdict":"UNREVIEWED","note":""})
    return result

def evaluate(source):
    rows=review_rows(source)
    probes=[]
    for row in rows:
        for role,question in (("means",f'{row["means"]}は何をするもの？'),
                              ("agent",f'{row["subject"]}は何によって行う？')):
            match=lookup(source,question)
            found=bool(match and match["line"]==row["line"] and
                       match["segment"]==row["segment"])
            probes.append({"id":row["id"],"role":role,"question":question,
                           "hit_exact_source":found,
                           "match_line":match["line"] if match else None})
    return {"version":"v0.3.7.8","candidate_count":len(rows),
            "human_reviewed":0,"correct":None,"ambiguous":None,"incorrect":None,
            "precision":None,"probes":len(probes),
            "source_hit_count":sum(x["hit_exact_source"] for x in probes),
            "source_hit_rate":(sum(x["hit_exact_source"] for x in probes)/len(probes)
                               if probes else None),
            "review":rows,"query_probes":probes}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--corpus",default="data/data-nagato.txt")
    p.add_argument("--report",default="results/persona_review_v0378.json")
    p.add_argument("--csv",default="results/persona_review_v0378.csv")
    a=p.parse_args()
    report=evaluate(a.corpus)
    target=Path(a.report);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    c=Path(a.csv);c.parent.mkdir(parents=True,exist_ok=True)
    with c.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=("id","line","segment","original","subject","means","predicate","marker","verdict","note"))
        writer.writeheader();writer.writerows(report["review"])
    print(json.dumps({k:v for k,v in report.items() if k not in ("review","query_probes")},ensure_ascii=False,indent=2))
    print("json:",target)
    print("csv:",c)
if __name__=="__main__":main()
