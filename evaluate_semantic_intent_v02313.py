"""Side-by-side purpose-controller diagnostic: seen development vs fresh holdout."""
import argparse,json
from pathlib import Path
from collections import defaultdict
from purpose_confidence_v02311 import DSS,respond as baseline
from semantic_intent_normalizer_v02313 import respond as normalized
from prepare_purpose_generalization_v02312 import fixture as development,SEQUENCES
from purpose_fresh_holdout_v02313 import fixture as fresh,FRESH_SEQUENCES

def evaluate_single(rows,fn):
    results=[]
    for case in rows:
        d=DSS()
        if fn is normalized:
            d,action,_,trace=fn(d,case["text"])
        else:
            d,action,_=fn(d,case["text"])
            trace={"raw":case["text"],"normalized":case["text"],"rules":[]}
        correct=action==case["expected_action"] and d.purpose==case["expected_purpose"]
        results.append({"id":case["id"],"expected_action":case["expected_action"],
                        "expected_purpose":case["expected_purpose"],
                        "predicted_action":action,"predicted_purpose":d.purpose,
                        "state":d.state,"confidence":d.confidence,"correct":correct,
                        "trace":trace})
    return results

def evaluate_multi(rows,fn):
    output=[]
    for case in rows:
        d=DSS();actions=[]
        for text in case["turns"]:
            if fn is normalized:d,action,_,_=fn(d,text)
            else:d,action,_=fn(d,text)
            actions.append(action)
        expected=case.get("expected_actions",case.get("actions"))
        goal=case.get("expected_purpose",case.get("purpose"))
        output.append({"id":case["id"],"actions":actions,"purpose":d.purpose,
                       "correct":actions==expected and d.purpose==goal})
    return output

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",default="results/semantic_intent_normalization_v02313.json")
    args=ap.parse_args()
    report={}
    for split,rows,multi in (("development_seen",development(),SEQUENCES),
                             ("fresh_holdout",fresh(),FRESH_SEQUENCES)):
        for name,fn in (("baseline",baseline),("normalized",normalized)):
            single=evaluate_single(rows,fn)
            seq=evaluate_multi(multi,fn)
            key=f"{split}/{name}"
            report[key]={"single":single,"multi":seq,
                         "single_correct":sum(r["correct"] for r in single),
                         "single_total":len(single),
                         "multi_correct":sum(r["correct"] for r in seq),
                         "multi_total":len(seq)}
            print(f'{key}: single={report[key]["single_correct"]}/{len(single)} '
                  f'multi={report[key]["multi_correct"]}/{len(seq)}')
            for r in single:
                if not r["correct"]:
                    print(f'  FAIL {r["id"]}: {r["predicted_purpose"]}/{r["predicted_action"]}'
                          f' rules={r["trace"]["rules"]}')
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved:",out)
if __name__=="__main__":main()
