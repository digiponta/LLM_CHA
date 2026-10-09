"""v0.2.30.2: varied, topic-grounded two-sentence continuation SFT.

All 12 prompts are unchanged. Each new response contains a topical opening
and a second on-topic sentence. No holdout answers are used for training.
"""
import argparse,json
from pathlib import Path
from prepare_topic_grounded_v02290 import TRAIN,HOLDOUT

# Two different, human-authored continuations for each training topic.
CONTINUATIONS={
 "宇宙探査":[
  "探査機が送る観測データから、遠くの天体の環境を少しずつ理解できる。",
  "例えば惑星の大気を調べると、形成の歴史を推測する手掛かりになる。"],
 "カレー":[
  "香辛料を少し変えるだけでも、香りと辛さの印象が変化する。",
  "例えば玉ねぎをじっくり炒めると、味に甘みと深みが加わる。"],
 "クラシック音楽":[
  "旋律を受け渡す楽器に注目すると、曲の展開が分かりやすい。",
  "例えば同じ旋律でも演奏の速さで、感じる雰囲気が変わる。"],
 "ゲーム開発":[
  "操作してすぐ反応が返るようにすると、遊びやすさを確かめられる。",
  "例えば小さなステージを先に作ると、面白さを早期に試せる。"],
 "歴史小説":[
  "登場人物の判断を時代背景と重ねると、物語の緊張感が増す。",
  "例えば史実と創作を比べると、作者が何を描きたいか考えられる。"],
 "写真撮影":[
  "光の向きを変えるだけで、被写体の立体感が変わる。",
  "例えば夕方の柔らかい光を使うと、色の印象も違って見える。"],
}
OPENERS=("まず、","もう一つは、")
def build():
    if set(TRAIN)&set(HOLDOUT):raise ValueError("topic split overlap")
    if set(TRAIN)!=set(CONTINUATIONS):raise ValueError("missing continuation topic")
    rows=[]
    for topic,originals in TRAIN.items():
        if len(originals)!=2 or len(CONTINUATIONS[topic])!=2:
            raise ValueError("expected 2 examples per topic")
        for i,old in enumerate(originals):
            # No canned prefix. Original substantive first sentence is preserved.
            answer=old+" "+OPENERS[i]+CONTINUATIONS[topic][i]
            question=(f"{topic}について話を続けて" if i==0
                      else f"{topic}の面白いところを教えて")
            rows.append({"user":"人: "+question,"assistant":answer})
    return rows
def validate(rows):
    if len(rows)!=12:raise ValueError("expected 12 rows")
    for row in rows:
        topic=next((x for x in TRAIN if row["user"].startswith("人: "+x)),None)
        if not topic:raise ValueError("unexpected topic")
        if topic not in row["assistant"]:raise ValueError("topic absent")
        if row["assistant"].count("。")<2:raise ValueError("not two-sentence response")
    return len(rows)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="data/topic_continuation_v02302/train_preformatted.jsonl")
    a=p.parse_args()
    rows=build();validate(rows)
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text("".join(json.dumps(row,ensure_ascii=False)+"\n" for row in rows),encoding="utf-8")
    print(f"Validated two-sentence topical continuations: {len(rows)}/12 -> {dest}")
if __name__=="__main__":main()
