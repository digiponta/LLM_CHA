"""Supplement exact topic metric with independent lexical continuation proxies.

Does NOT equate lexical match with semantic correctness. All scores are on
raw generated answers only, without copying the input topic into the output.
"""
import argparse,json,re
from collections import defaultdict
from pathlib import Path
from prepare_topic_continuation_v02302 import CONTINUATIONS

# Diagnostic anchor words are deliberately absent from the primary fixture
# in many cases, but shared words can occur in unrelated outputs.
ANCHORS={
 "宇宙探査":("探査機","観測","惑星","大気","天体"),
 "カレー":("香辛料","玉ねぎ","辛さ","香り","料理"),
 "クラシック音楽":("旋律","演奏","楽器","交響曲","音楽"),
 "ゲーム開発":("ゲーム","操作","ステージ","遊び","開発"),
 "歴史小説":("歴史","時代","小説","史実","人物"),
 "写真撮影":("写真","撮影","光","構図","被写体"),
 "深海探査":("深海","海底","探査","水圧","海洋"),
 "陶芸":("陶芸","粘土","焼成","器","窯"),
 "ミント栽培":("ミント","栽培","葉","香り","植物"),
 "夜景撮影":("夜景","撮影","露出","光","三脚"),
 "自転車旅行":("自転車","旅行","走行","道","休憩"),
 "天体観測":("天体","観測","星","望遠鏡","夜空"),
}
def metrics(topic,answer):
    if topic not in ANCHORS:raise ValueError(f"unknown topic {topic}")
    text=re.sub(r"\s+","",answer)
    sentences=[s.strip() for s in re.split(r"[。！？!?]+",text) if s.strip()]
    hits=[s for s in sentences if any(t in s for t in ANCHORS[topic])]
    return {"sentence_count":len(sentences),
            "two_plus_sentences":len(sentences)>=2,
            "lexical_topic_coverage":len(hits)>0,
            "lexical_topic_in_second_sentence":len(sentences)>=2 and any(
                t in sentences[1] for t in ANCHORS[topic]),
            "topic_exact":topic in text}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/topic_continuation_compare_v02302.jsonl")
    p.add_argument("--out",default="results/topic_continuation_metrics_v02302.jsonl")
    a=p.parse_args()
    src=Path(a.input)
    if not src.is_file():p.error("run evaluate_topic_grounded_v02290.py with --out first")
    rows=[json.loads(s) for s in src.read_text(encoding="utf-8-sig").splitlines() if s.strip()]
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    summary=defaultdict(lambda:{"n":0,"topic":0,"two":0,"second":0})
    with dest.open("w",encoding="utf-8") as fp:
        for row in rows:
            v=metrics(row["topic"],row["raw_answer"])
            record={"model":row["model"],"split":row["split"],"topic":row["topic"],
                    "answer":row["raw_answer"],**v}
            fp.write(json.dumps(record,ensure_ascii=False)+"\n")
            s=summary[(row["model"],row["split"])]
            s["n"]+=1;s["topic"]+=int(v["lexical_topic_coverage"])
            s["two"]+=int(v["two_plus_sentences"])
            s["second"]+=int(v["lexical_topic_in_second_sentence"])
    for (model,split),s in summary.items():
        print(f'{model}/{split}: lexical-topic={s["topic"]}/{s["n"]} '
              f'two-sentences={s["two"]}/{s["n"]} '
              f'second-sentence-topic={s["second"]}/{s["n"]}')
    print("Saved:",dest)
if __name__=="__main__":main()
