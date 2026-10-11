"""v0.2.33.68: experimental epistemic style calibration and review worksheet.

Labels are heuristic stylistic suggestions, never Truth State. '可能性' alone is
not evidence that a passage is speculative. Human gold labels must be supplied
separately before reporting any accuracy, precision, recall, or F1.
"""
import argparse,json,re
from pathlib import Path
from corpus_context_classification_v023367 import mentions,classify

LABELS=frozenset({"HYPOTHESIS","ANALOGY","OPINION","STRUCTURAL_CANDIDATE","CONTEXT_ONLY"})

def classify_v68(sentence):
    labels=[]
    if re.search(r"かもしれない|おそらく|多分|推測|仮説|不明|だろう|としたら",sentence):
        labels.append("HYPOTHESIS")
    # bare "可能性" can be technical language, not epistemic uncertainty
    if re.search(r"アナロジ|類似|例え|たとえ|ようなもの|みたいな",sentence):
        labels.append("ANALOGY")
    if re.search(r"私見|私は思う|と考える|観点|見方",sentence):
        labels.append("OPINION")
    if not labels:
        from structural_semantic_consistency_v023359 import parse,clean
        labels=["STRUCTURAL_CANDIDATE"] if parse(clean(sentence)) else ["CONTEXT_ONLY"]
    return labels

def dataset(path,concept):
    rows=[]
    for item in mentions(path,concept):
        rows.append({"mention_start":item["mention_start"],
            "context":item["context"],"context_sha256":item["context_sha256"],
            "baseline_labels":classify(item["context"]),
            "candidate_labels":classify_v68(item["context"]),
            "gold_labels":None,"review_status":"UNREVIEWED"})
    return {"version":"v0.2.33.68","concept":concept,
        "source_sha256":rows and mentions(path,concept)[0]["file_sha256"],
        "sample_count":len(rows),"reviewed_count":0,
        "metrics":None,"rows":rows,
        "note":"No accuracy is reported without independently reviewed gold labels."}

def evaluate_reviewed(rows):
    reviewed=[r for r in rows if r.get("review_status")=="REVIEWED"]
    if not reviewed:return {"reviewed_count":0,"metrics":None}
    for r in reviewed:
        gold=r.get("gold_labels")
        if not isinstance(gold,list) or not gold or any(g not in LABELS for g in gold):
            raise ValueError("reviewed gold_labels must be a nonempty allowed label list")
    def scoring(key):
        tp=fp=fn=0
        for r in reviewed:
            pred=set(r[key]); gold=set(r["gold_labels"])
            tp+=len(pred&gold);fp+=len(pred-gold);fn+=len(gold-pred)
        precision=tp/(tp+fp) if tp+fp else 0
        recall=tp/(tp+fn) if tp+fn else 0
        return {"tp":tp,"fp":fp,"fn":fn,"micro_precision":precision,
                "micro_recall":recall,
                "micro_f1":2*precision*recall/(precision+recall) if precision+recall else 0}
    return {"reviewed_count":len(reviewed),
            "metrics":{"baseline":scoring("baseline_labels"),
                       "candidate":scoring("candidate_labels")}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="data/data-nagato.txt")
    p.add_argument("--concept",default="量子力学")
    p.add_argument("--out",default="results/epistemic_calibration_v023368.json")
    p.add_argument("--score",help="Existing edited review worksheet JSON; read-only")
    args=p.parse_args()
    if args.score:
        saved=json.loads(Path(args.score).read_text(encoding="utf8"))
        results=evaluate_reviewed(saved["rows"])
        print(json.dumps(results,ensure_ascii=False,indent=2))
        return
    out=Path(args.out)
    if out.exists():raise FileExistsError(f"Will not overwrite existing worksheet: {out}")
    obj=dataset(args.source,args.concept)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf8")
    print(f"Captured {obj['sample_count']} mention contexts; gold labels unreviewed; metrics unavailable.")
    print(out)

if __name__=="__main__":main()
