"""Diagnose intent generalization and heuristic confidence, no retraining."""
import argparse,json
from pathlib import Path
from collections import defaultdict
from purpose_confidence_v02311 import DSS,respond
from prepare_purpose_generalization_v02312 import fixture,SEQUENCES

def evaluate_single(rows):
    results=[]
    for r in rows:
        state,action,_=respond(DSS(),r["text"])
        expected=r["expected_purpose"]
        correct=action==r["expected_action"] and state.purpose==expected
        # A confidence score is used for selective calibration only for
        # requests expecting an explicit purpose; ambiguous requests
        # have no correct purpose category and are reported separately.
        results.append({**r,"predicted_action":action,"predicted_purpose":state.purpose,
                        "state":state.state,"confidence":state.confidence,
                        "correct":correct})
    return results

def reliability(rows,bins=((0,0.5),(0.5,0.8),(0.8,1.0000001))):
    classified=[r for r in rows if r["expected_purpose"] is not None]
    out=[]
    for low,high in bins:
        group=[r for r in classified if low<=r["confidence"]<high]
        n=len(group)
        out.append({"low":low,"high":high,"count":n,
                    "mean_confidence":sum(r["confidence"] for r in group)/n if n else None,
                    "empirical_accuracy":sum(r["correct"] for r in group)/n if n else None})
    return out

def evaluate_sequences(cases):
    results=[]
    for case in cases:
        d=DSS();actions=[]
        for statement in case["turns"]:
            d,action,_=respond(d,statement);actions.append(action)
        results.append({"id":case["id"],"actions":actions,
                        "purpose":d.purpose,
                        "correct":actions==case["expected_actions"] and
                                  d.purpose==case["expected_purpose"]})
    return results

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",default="results/purpose_generalization_v02312.json")
    a=ap.parse_args()
    singles=evaluate_single(fixture())
    sequences=evaluate_sequences(SEQUENCES)
    bins=reliability(singles)
    by_kind=defaultdict(lambda:{"correct":0,"count":0})
    for r in singles:
        kind=r["id"].split("-")[0]
        by_kind[kind]["count"]+=1
        by_kind[kind]["correct"]+=int(r["correct"])
        print(f'{r["id"]}: expected={r["expected_purpose"]}/{r["expected_action"]} '
              f'predicted={r["predicted_purpose"]}/{r["predicted_action"]} '
              f'confidence={r["confidence"]:.2f} {"PASS" if r["correct"] else "FAIL"}')
    for r in sequences:
        print(f'multi {r["id"]}: {"PASS" if r["correct"] else "FAIL"} {r["actions"]}')
    accuracy=sum(x["correct"] for x in singles)/len(singles)
    seq_acc=sum(x["correct"] for x in sequences)/len(sequences)
    print(f"Single-turn accuracy: {sum(x['correct'] for x in singles)}/{len(singles)} ({accuracy:.1%})")
    print(f"Multi-turn success: {sum(x['correct'] for x in sequences)}/{len(sequences)} ({seq_acc:.1%})")
    for kind,s in by_kind.items():
        print(f'{kind}: {s["correct"]}/{s["count"]}')
    for b in bins:
        print(f'confidence [{b["low"]:.1f},{b["high"]:.1f}): '
              f'n={b["count"]} mean={b["mean_confidence"]} '
              f'accuracy={b["empirical_accuracy"]}')
    result={"single":singles,"sequences":sequences,"reliability":bins,
            "single_accuracy":accuracy,"sequence_success":seq_acc,
            "by_kind":dict(by_kind)}
    target=Path(a.out);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved:",target)
if __name__=="__main__":main()
