"""v0.2.18: derive a small Japanese LM corpus from training split ONLY.

No test/val records are used. This is a controlled pilot, not clean-web
pretraining. Source provenance remains RealPersonaChat with its license.
"""
from __future__ import annotations
import argparse,json,random
from pathlib import Path

def build(source:Path,dest:Path,limit:int=5000,seed:int=42):
    rows=[json.loads(s) for s in source.read_text(encoding="utf-8").splitlines() if s.strip()]
    rng=random.Random(seed);rng.shuffle(rows)
    selected=rows[:limit]
    # User and assistant text from TRAIN ONLY. These are short utterances,
    # so 'foundation' means a pilot, not a broad language corpus.
    parts=[]
    for row in selected:
        answer=row.get("assistant","")
        if not isinstance(answer,str) or len(answer.strip())<12:continue
        parts.append(answer.strip()+"。\n")
    if not parts:raise ValueError("No usable training text")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text("".join(parts),encoding="utf-8")
    return {"rows_seen":len(selected),"sentences":len(parts),"characters":sum(map(len,parts)),
            "source":str(source),"seed":seed}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/dialogue_generalization_v0212/train.jsonl"))
    p.add_argument("--output",type=Path,default=Path("data/japanese_foundation_v0218.txt"))
    p.add_argument("--max-rows",type=int,default=5000)
    a=p.parse_args()
    print(json.dumps(build(a.source,a.output,a.max_rows),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
