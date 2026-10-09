"""v0.2.24: separate repeated context examples from ordinary replay.

Existing SFT trainer deduplicates input lines; pass six distinct context
pairs through --expansion-data and use --expansion-weight for explicit replay.
"""
from __future__ import annotations
import argparse,json,random
from pathlib import Path
from prepare_context_conditional_v0223 import TOPICS,HOLDOUT,make

def build(output:Path,replay:Path,weight:int=60,replay_limit:int=3000,seed:int=42):
    if weight<1 or replay_limit<0:raise ValueError("weight must be positive and replay limit nonnegative")
    contexts=[make(t) for t in TOPICS]
    heldout=[make(t) for t in HOLDOUT]
    if {r["user"] for r in contexts}&{r["user"] for r in heldout}:raise ValueError("train/val leakage")
    excluded=("写真","夜景","撮影","カメラ","園芸","ミント","植物","庭","photo","garden","mint")
    background=[]
    if replay_limit:
        for line in replay.read_text(encoding="utf-8").splitlines():
            if not line.strip():continue
            row=json.loads(line)
            if not isinstance(row.get("user"),str) or not isinstance(row.get("assistant"),str):continue
            if any(term in (row["user"]+" "+row["assistant"]).lower() for term in excluded):continue
            background.append(row)
        random.Random(seed).shuffle(background)
        background=background[:replay_limit]
    if len(background)<2:raise ValueError("Need at least 2 replay pairs for trainer")
    output.mkdir(parents=True,exist_ok=True)
    for name,rows in (("train",background),("context",contexts),("val",heldout)):
        with (output/(name+".jsonl")).open("w",encoding="utf-8") as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    expected=weight*len(contexts)+len(background)
    metrics={"unique_context_pairs":len(contexts),"context_weight":weight,"expected_context_exposures":weight*len(contexts),
             "replay_pairs":len(background),"expected_rows_before_anchors":expected,
             "context_fraction_before_anchors":round(weight*len(contexts)/expected,6),
             "holdout_pairs":len(heldout),"seed":seed}
    (output/"manifest.json").write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return metrics
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,default=Path("data/context_weighted_v0224"))
    p.add_argument("--replay",type=Path,default=Path("data/dialogue_generalization_v0212/train.jsonl"))
    p.add_argument("--context-weight",type=int,default=60)
    p.add_argument("--replay-limit",type=int,default=3000)
    a=p.parse_args()
    print(json.dumps(build(a.output,a.replay,a.context_weight,a.replay_limit),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
