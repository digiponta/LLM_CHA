"""Diagnose selection-gate shadow results without touching test data or gate.

Reads the privacy-preserving v0.13.58.83.10 report. It does not train,
select thresholds, or change any inference behavior.
"""
import argparse,collections,json
from pathlib import Path

VALID={"ACCEPT_CANDIDATE","MANUAL_REVIEW_REQUIRED","REJECT"}
def analyze(report):
    rows=report.get("rows",[])
    if report.get("status")!="AI_PROVISIONAL_SHADOW_EVALUATION":
        raise ValueError("EXPECTED_AI_PROVISIONAL_SHADOW_REPORT")
    if len(rows)!=report.get("cases") or not rows:
        raise ValueError("ROW_COUNT_MISMATCH")
    decisions=collections.Counter()
    reasons=collections.Counter()
    strata=collections.defaultdict(lambda:collections.Counter())
    ids=collections.defaultdict(list)
    for row in rows:
        d=row.get("decision")
        if d not in VALID:raise ValueError("UNKNOWN_DECISION")
        label=row.get("ai_provisional_suitable")
        if type(label) is not bool:raise ValueError("INVALID_LABEL")
        decisions[d]+=1
        group="provisional_positive" if label else "provisional_negative"
        strata[group][d]+=1
        for why in set(row.get("reasons",[])):
            reasons[why]+=1
            strata[group]["reason:"+why]+=1
        ids[d].append(row["id"])
    review=decisions["MANUAL_REVIEW_REQUIRED"]
    positives=sum(1 for row in rows if row["ai_provisional_suitable"])
    return {
        "status":"DIAGNOSTIC_ONLY_NO_GATE_CHANGE",
        "case_count":len(rows),
        "label_provenance":"AI_PROVISIONAL_NOT_HUMAN_VERIFIED",
        "test_split_for_diagnostics_only":True,
        "no_test_threshold_tuning":True,
        "decision_counts":dict(decisions),
        "reason_counts":dict(reasons.most_common()),
        "by_label":{k:dict(v) for k,v in strata.items()},
        "review_fraction":review/len(rows),
        "positive_count":positives,
        "positive_review_fraction":strata["provisional_positive"]["MANUAL_REVIEW_REQUIRED"]/positives if positives else None,
        "decision_case_ids":dict(ids),
        "interpretation":"No tuning, auto-acceptance, or live deployment is authorized by these diagnostic counts."
    }
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/rse_shadow_evaluation_v013588310.json")
    p.add_argument("--output",default="results/rse_shadow_diagnostics_v013588311.json")
    a=p.parse_args()
    result=analyze(json.loads(Path(a.input).read_text(encoding="utf-8-sig")))
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="decision_case_ids"},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
