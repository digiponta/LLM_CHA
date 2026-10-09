"""v0.2.30.1: genuinely changed topic-prefix supervision rows.

Preserves prompts and factual core, checks every old/new pair differs.
"""
import argparse,json
from pathlib import Path
from prepare_topic_grounded_v02290 import TRAIN,HOLDOUT
from prepare_topic_grounded_preformatted_v02291 import convert

def build(old_rows):
    if set(TRAIN)&set(HOLDOUT):raise ValueError("train/holdout overlap")
    new_rows=[]
    for row in old_rows:
        user,answer=row["user"],row["assistant"]
        topic=next((t for t in TRAIN if user.startswith(t)),None)
        if topic is None:raise ValueError(f"unrecognized training topic: {user}")
        # The old answer is preserved verbatim after an explicit topic-conditioned lead.
        prefix=f"{topic}について説明するね。"
        revised=prefix+answer
        if revised==answer or not revised.startswith(prefix):
            raise ValueError("unchanged or invalid topic-prefix answer")
        new_rows.append({"user":user,"assistant":revised})
    if len(new_rows)!=12 or len(old_rows)!=12:raise ValueError("expected exactly 12 rows")
    original_pairs=convert(old_rows)
    result=convert(new_rows)
    changed=sum(x["assistant"]!=y["assistant"] for x,y in zip(original_pairs,result))
    if changed!=12:raise ValueError(f"expected 12 changed answers, got {changed}")
    for x,y in zip(original_pairs,result):
        if x["user"]!=y["user"]:raise ValueError("prompts changed")
        if not y["assistant"].endswith(x["assistant"]):raise ValueError("original content not preserved")
    return result,changed

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="data/topic_grounded_v02290/train.jsonl")
    p.add_argument("--output",default="data/topic_prefix_v02301/train_preformatted.jsonl")
    a=p.parse_args()
    src=Path(a.source)
    if not src.is_file():p.error("run prepare_topic_grounded_v02290.py first")
    old=[json.loads(s) for s in src.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    rows,changed=build(old)
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
    print(f"Topic prefix changed: {changed}/12; saved: {dest}")
if __name__=="__main__":main()
