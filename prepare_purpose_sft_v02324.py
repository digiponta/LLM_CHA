"""v0.2.32.4 purpose-conditioned SFT data; fixed disjoint topic partitions.

Hand-authored toy curriculum, NOT a large-scale natural language dataset.
Split by topic, never shuffle rows across topics.
"""
import json,argparse
from pathlib import Path
TOPICS={
 "train":["Python","LLM","GPU","CPU"],
 "val":["データベース","センサー"],
 "test":["画像認識","ネットワーク"],
}
TASKS=[
 ("learning","{t}を勉強したい","{t}を学ぶなら、基本概念を確認し、小さな例を試してから応用に進みましょう。"),
 ("learning","{t}の基礎を教えて","{t}の基本を順番に整理しましょう。まず目的と重要な用語を確認します。"),
 ("development","{t}を使って開発したい","{t}で開発するなら、要件を決めて、小さな試作品を作り、動作を確認しましょう。"),
 ("development","{t}を自作したい","{t}を自作するには、必要な機能を整理し、最小構成から実装して検証します。"),
 ("troubleshooting","{t}の動作がおかしい","{t}の問題を調べるために、再現手順、エラー表示、直前の変更を教えてください。"),
 ("troubleshooting","{t}のエラーを直したい","{t}のエラーを切り分けましょう。実際のエラーメッセージと実行環境を確認します。"),
 ("casual","{t}について雑談したい","{t}の話をしましょう。最近どんなことが気になっていますか？"),
 ("casual","{t}について気軽に話そう","{t}について話しましょう。どんな話題から始めますか？"),
]
PLAN=("learning,development","{t}を勉強してから開発したい",
      "{t}について、まず基本を学び、次に小さな試作品を作って動作を確認しましょう。")
PURPOSE_JA={"learning":"学習","development":"開発","troubleshooting":"問題解決","casual":"雑談",
            "learning,development":"学習 → 開発"}
# Replay examples use a separate legacy prompt without purpose fields.
REPLAY=[
 {"prompt":"人: こんにちは\nAI: ","answer":"こんにちは。"},
 {"prompt":"人: ありがとう\nAI: ","answer":"どういたしまして。"},
 {"prompt":"人: あなたは誰ですか\nAI: ","answer":"長門有希。"},
 {"prompt":"人: おやすみ\nAI: ","answer":"おやすみなさい。"},
]
def prompt(topic,purpose,user):
    return f"話題: {topic}\n目的: {PURPOSE_JA[purpose]}\n人: {user}\nAI: "
def build():
    rows={}
    for split,topics in TOPICS.items():
        current=[]
        for topic in topics:
            for i,(purpose,question,answer) in enumerate(TASKS+ [PLAN]):
                utterance=question.format(t=topic)
                current.append({"id":f"{split}-{topic}-{i}","split":split,
                                "topic":topic,"purpose":purpose,"user":utterance,
                                "prompt":prompt(topic,purpose,utterance),
                                "answer":answer.format(t=topic)})
        rows[split]=current
    return rows
def validate(rows):
    topics={k:{x["topic"] for x in v} for k,v in rows.items()}
    assert not any(topics[a]&topics[b] for a,b in
                   (("train","val"),("train","test"),("val","test")))
    assert all(x["prompt"].endswith("AI: ") and x["answer"] for v in rows.values() for x in v)
    assert len({x["prompt"] for v in rows.values() for x in v})==sum(map(len,rows.values()))
    return {"counts":{k:len(v) for k,v in rows.items()},
            "topics":{k:sorted(v) for k,v in topics.items()}}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out-dir",default="data/purpose_sft_v02324")
    a=p.parse_args()
    rows=build(); info=validate(rows)
    dest=Path(a.out_dir);dest.mkdir(parents=True,exist_ok=True)
    for split,items in rows.items():
        with (dest/f"{split}.jsonl").open("w",encoding="utf-8") as f:
            for item in items:f.write(json.dumps(item,ensure_ascii=False)+"\n")
    (dest/"replay.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in REPLAY),encoding="utf-8")
    (dest/"manifest.json").write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(info,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
