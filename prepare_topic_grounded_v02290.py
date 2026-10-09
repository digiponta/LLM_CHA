"""Build strictly topic-disjoint train/holdout SFT and evaluation fixtures."""
from __future__ import annotations
import argparse,json,random
from pathlib import Path

TRAIN={
"宇宙探査":["宇宙探査なら、探査機が未知の惑星を調べる過程が面白いね。","宇宙探査では、観測機器から届くデータを使って惑星の特徴を調べるよ。"],
"カレー":["カレーでは、香辛料と野菜の組み合わせで風味が変わるね。","カレーを作るなら、香辛料を炒めて香りを引き出す方法があるよ。"],
"クラシック音楽":["クラシック音楽では、楽器の重なりや旋律の変化を楽しめるよ。","クラシック音楽なら、交響曲や室内楽の違いを聴き比べるのも面白いね。"],
"ゲーム開発":["ゲーム開発では、操作感と画面の反応を繰り返し調整するよ。","ゲーム開発なら、まず小さな試作品で遊びの仕組みを検証するといいね。"],
"歴史小説":["歴史小説では、時代背景と登場人物の選択を楽しめるね。","歴史小説なら、史実を調べて物語との違いを考えるのも面白いよ。"],
"写真撮影":["写真撮影では、光の向きや構図で印象が変わるよ。","写真撮影なら、同じ被写体を時間帯を変えて撮り比べるといいね。"],
}
HOLDOUT={
"深海探査":["深海探査では、水圧に耐える探査機で海底の様子を観測するよ。"],
"陶芸":["陶芸では、粘土の成形と焼成によって器の表情が変わるね。"],
"ミント栽培":["ミント栽培では、葉の香りと生育の変化を観察できるよ。"],
"夜景撮影":["夜景撮影では、露出時間と手ぶれ対策が重要になるよ。"],
"自転車旅行":["自転車旅行なら、距離と休憩場所を考えて走行計画を立てるといいね。"],
"天体観測":["天体観測では、空の暗さと観測時刻を調べることが大切だよ。"],
}
PROMPT_TEMPLATES=["{topic}について話を続けて","{topic}の面白いところを教えて",
                  "最近{topic}に興味があります。何か話して"]
def build(train=TRAIN,holdout=HOLDOUT):
    if set(train)&set(holdout):raise ValueError("topic overlap")
    rows=[]
    for split,topics in (("train",train),("holdout",holdout)):
        for topic,answers in topics.items():
            for i,answer in enumerate(answers):
                if topic not in answer:raise ValueError(f"missing topic in answer: {topic}")
                prompt=PROMPT_TEMPLATES[i%len(PROMPT_TEMPLATES)].format(topic=topic)
                rows.append({"split":split,"topic":topic,"user":prompt,"assistant":answer,
                             "source":"curated_v02290","answer_mentions_topic":True})
    return rows
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out-dir",default="data/topic_grounded_v02290")
    a=p.parse_args()
    dest=Path(a.out_dir);dest.mkdir(parents=True,exist_ok=True)
    rows=build()
    for split in ("train","holdout"):
        path=dest/(split+".jsonl")
        path.write_text("".join(json.dumps({"user":r["user"],"assistant":r["assistant"]},
                                          ensure_ascii=False)+"\n" for r in rows if r["split"]==split),encoding="utf-8")
        print(split,":",sum(r["split"]==split for r in rows),path)
    fixture=dest/"eval.jsonl"
    fixture.write_text("".join(json.dumps({"split":r["split"],"topic":r["topic"],
                                           "prompt":r["user"],"reference":r["assistant"]},
                                          ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
    print("Evaluation fixture:",fixture)
if __name__=="__main__":main()
