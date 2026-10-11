"""v0.2.33.71 offline epistemic classifier and prospective evaluation worksheet.

No updates to live chat runtime, Semantic Memory, Truth State, or model weights.
The eight v70 holdout labels have been seen during development: do not use them
as an independent test of the new v71 rules.
"""
import argparse,hashlib,json,re
from pathlib import Path
from corpus_context_classification_v023367 import classify as classify_v67
from epistemic_calibration_v023368 import classify_v68,LABELS
from epistemic_holdout_v023370 import classify_v70

def classify_v71(sentence):
    labels=classify_v70(sentence)
    # Anchored, explicit first-person stance cues, not generic possibility words.
    stance=r"(?:私の|自分の)(?:解釈|見解|考え)(?:では|だと|として)|私見では|個人的には"
    if re.search(stance,sentence):
        if labels==["CONTEXT_ONLY"]:labels=[]
        if "OPINION" not in labels:labels.append("OPINION")
    return labels or ["CONTEXT_ONLY"]

# Prospective *source texts*, not human-adjudicated labels. Fixed before the
# next user evaluation, but authored with awareness of previous error modes.
PROBES=(
    "私の見解では、その条件は成立しない。",
    "可能性の分布を用いて確率を計算する。",
    "この主張は暫定的な仮説だろう。",
    "見方を変えれば、世界は巨大な時計のようなものだ。",
    "個人的にはこの定式化が自然だと思う。",
    "粒子の振る舞いを数式で記述する。",
    "これは単なる例えであり、物理法則ではない。",
    "その現象は不明で、別の解釈があるかもしれない。",
    "私の解釈では、宇宙は舞台のようなものだ。",
    "測定値には統計的なばらつきがある。",
    "仮説ではなく、条件付きのモデルとして定義する。",
    "可能性という単語を扱う文法の説明である。",
)

def worksheet():
    rows=[]
    for i,context in enumerate(PROBES,1):
        rows.append({"sample_id":f"P{i:02d}","context":context,
                     "context_sha256":hashlib.sha256(context.encode("utf8")).hexdigest(),
                     "v67_labels":classify_v67(context),
                     "v68_labels":classify_v68(context),
                     "v70_labels":classify_v70(context),
                     "v71_labels":classify_v71(context),
                     "gold_labels":None,"review_status":"UNREVIEWED"})
    return {"version":"v0.2.33.71","origin":"prospectively-fixed-development-probes",
            "disclosure":"Designed after observing errors in v70; NOT a final independent benchmark.",
            "rows":rows}

def evaluate(data):
    if data.get("version")!="v0.2.33.71" or not isinstance(data.get("rows"),list):
        raise ValueError("bad_worksheet")
    original=worksheet()["rows"]
    rows=data["rows"]
    if len(rows)!=len(original):raise ValueError("changed_row_count")
    reviewed=[]
    keys=("sample_id","context","context_sha256","v67_labels","v68_labels","v70_labels","v71_labels")
    for a,b in zip(rows,original):
        if any(a.get(key)!=b[key] for key in keys):raise ValueError("modified_probes_or_predictions")
        state=a.get("review_status");gold=a.get("gold_labels")
        if state=="UNREVIEWED":
            if gold is not None:raise ValueError("unreviewed_gold_present")
        elif state=="REVIEWED":
            if (not isinstance(gold,list) or not gold or len(gold)!=len(set(gold)) or
                any(label not in LABELS for label in gold)):
                raise ValueError("invalid_gold")
            reviewed.append(a)
        else:raise ValueError("invalid_review_status")
    if not reviewed:return {"reviewed_count":0,"total_count":len(rows),"metrics":None}
    results={}
    for key in ("v67_labels","v68_labels","v70_labels","v71_labels"):
        tp=fp=fn=0
        for r in reviewed:
            pred=set(r[key]);gold=set(r["gold_labels"])
            tp+=len(pred&gold);fp+=len(pred-gold);fn+=len(gold-pred)
        precision=tp/(tp+fp) if tp+fp else 0.0
        recall=tp/(tp+fn) if tp+fn else 0.0
        results[key]={"tp":tp,"fp":fp,"fn":fn,"precision":precision,
                      "recall":recall,"micro_f1":
                      2*precision*recall/(precision+recall) if precision+recall else 0.0}
    return {"reviewed_count":len(reviewed),"total_count":len(rows),"metrics":results}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/epistemic_prospective_v023371.json")
    p.add_argument("--score")
    args=p.parse_args()
    if args.score:
        print(json.dumps(evaluate(json.loads(Path(args.score).read_text(encoding="utf8"))),
                         ensure_ascii=False,indent=2))
    else:
        target=Path(args.out);target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("x",encoding="utf8") as f:
            json.dump(worksheet(),f,ensure_ascii=False,indent=2)
        print(f"Prepared {len(PROBES)} unreviewed prospective examples: {target}")

if __name__=="__main__":main()
