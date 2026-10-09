"""Compare structure parser and vector-only estimator, field by field."""
import argparse,json
from pathlib import Path
from structured_purpose_holdout_v02316 import fixture
from structured_semantic_purpose_v02315 import extract,action_for
from semantic_purpose_estimator_v02314 import SemanticPurposeEstimator
from purpose_confidence_v02311 import topic_of

FIELDS=("topic","purposes","relation","polarity","action")
def evaluate(rows,mode,estimator):
    out=[]
    for gold in rows:
        if mode=="structured":
            s=extract(gold["text"],estimator)
            pred={"topic":s.topic,"purposes":s.purposes,
                  "relation":s.relation,"polarity":s.polarity,
                  "action":action_for(s)}
        elif mode=="vector":
            r=estimator.predict(gold["text"])
            purpose=[r["purpose"]] if r["accepted"] else []
            pred={"topic":topic_of(gold["text"]),"purposes":purpose,
                  "relation":"UNSPECIFIED","polarity":"POSITIVE",
                  "action":"HANDOFF" if purpose else "ASK_CLARIFICATION"}
        else:raise ValueError(mode)
        score={f:pred[f]==gold[f] for f in FIELDS}
        score["purpose_set"]=set(pred["purposes"])==set(gold["purposes"])
        score["all"]=all(score[f] for f in FIELDS)
        out.append({"id":gold["id"],"text":gold["text"],
                    "expected":gold,"predicted":pred,"score":score})
    return out

def summary(results):
    n=len(results)
    metrics={f:{"pass":sum(r["score"][f] for r in results),"total":n}
             for f in (*FIELDS,"purpose_set","all")}
    ambiguous=[r for r in results if not r["expected"]["purposes"]]
    overcommit=sum(bool(r["predicted"]["purposes"]) for r in ambiguous)
    metrics["overcommit"]={"count":overcommit,"denominator":len(ambiguous)}
    return metrics

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/structured_purpose_v02316.json")
    args=p.parse_args()
    est=SemanticPurposeEstimator()
    report={"dataset":"v0.2.31.6 prospective diagnostic; hand-labeled, small",
            "purpose_order_note":"exact purposes compares ordered lists; purpose_set ignores order"}
    for mode in ("vector","structured"):
        result=evaluate(fixture(),mode,est)
        metrics=summary(result)
        report[mode]={"metrics":metrics,"rows":result}
        print("\n"+mode)
        for name,values in metrics.items():
            print(f'{name}: {values}')
        for row in result:
            failed=[f for f in FIELDS if not row["score"][f]]
            if failed:print(f'FAIL {row["id"]}: {",".join(failed)}')
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved:",out)
if __name__=="__main__":main()
