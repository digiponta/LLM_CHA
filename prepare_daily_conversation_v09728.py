"""Export *train only* examples in the runtime's 人:/AI: text format.

No GPU training is invoked; holdout remains separate for evaluation.
"""
import argparse,json
from pathlib import Path
from daily_conversation_foundation_v09728 import dataset,audit

def export(directory):
    base=Path(directory)
    d=dataset()
    stats=audit(d)
    if not stats["ready_for_controlled_training"]:
        raise ValueError("Train/holdout leakage")
    base.mkdir(parents=True,exist_ok=True)
    for part in ("train","holdout"):
        path=base/("daily_conversation_"+part+"_v09728.jsonl")
        with path.open("w",encoding="utf-8") as f:
            for row in d[part]:
                sample={**row,"prompt":"人: "+row["input"]+"\nAI: ",
                        "completion":row["target"]}
                f.write(json.dumps(sample,ensure_ascii=False)+"\n")
    (base/"daily_conversation_audit_v09728.json").write_text(
        json.dumps(stats,ensure_ascii=False,indent=2),encoding="utf-8")
    return stats
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="data")
    args=p.parse_args()
    print(json.dumps(export(args.out),ensure_ascii=False,indent=2))
