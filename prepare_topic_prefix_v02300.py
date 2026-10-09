"""Prepare matched 12-row topic-prefix SFT corpus from v0.2.29.0 train only.

No holdout use. Keep same prompts, exposure count and trainer as v0.2.29.1.
"""
import argparse,json
from pathlib import Path
from prepare_topic_grounded_v02290 import TRAIN,HOLDOUT

def make_rows(train=TRAIN,holdout=HOLDOUT):
    if set(train)&set(holdout):raise ValueError("topic overlap")
    rows=[]
    for topic,answers in train.items():
        if len(answers)!=2:raise ValueError("expected exactly two replies per train topic")
        templates=(f"{topic}について話を続けて",
                   f"{topic}の面白いところを教えて")
        for question,answer in zip(templates,answers):
            if not answer.startswith(topic): 
                # Ensure a single explicit topic at response start. No label in prompt beyond user text.
                answer=topic+"について、"+answer
            rows.append({"user":"人: "+question,"assistant":answer})
    return rows

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="data/topic_prefix_v02300/train_preformatted.jsonl")
    a=p.parse_args()
    rows=make_rows()
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in rows),encoding="utf-8")
    print(f"Topic prefix training rows: {len(rows)} -> {dest}")
if __name__=="__main__":main()
