"""v0.2.23 contrastive-context SFT dataset; no synthetic targets in heldout train."""
from __future__ import annotations
import argparse,json,random
from pathlib import Path
TOPICS=[
("SF小説","宇宙探査","宇宙探査では、未知の惑星に向かう乗組員の判断が物語の鍵になるね。"),
("料理","カレー","カレーでは、野菜と香辛料の組み合わせで味や香りが変わるね。"),
("音楽","クラシック","クラシック音楽では、楽器の音色や演奏のテンポによって印象が変わるね。"),
("散歩","公園","公園の散歩では、木々や季節の花の変化を楽しめるね。"),
("プログラミング","ゲーム","ゲーム制作では、ルールを少し変えるだけで遊び方が変化するね。"),
("読書","歴史小説","歴史小説では、その時代の暮らしと登場人物の関係が面白いね。"),
]
HOLDOUT=[
("写真","夜景","夜景写真では、水面に映る光や街の明かりが印象的になるね。"),
("園芸","ミント","ミントの栽培では、葉の香りや成長の変化を観察できるね。"),
]
QUESTION="その話を続けて"
def make(topic):
    kind,detail,answer=topic
    return {"user":f"人: 最近、{kind}に興味があります\nAI: どんなものが好き？\n人: {detail}です\nAI: その話をもう少し聞かせて\n人: {QUESTION}",
            "assistant":answer}
def build(out:Path,replay:Path,repeat=60,replay_limit=3000,seed=42):
    if repeat<1 or replay_limit<0:raise ValueError("Invalid counts")
    rng=random.Random(seed);tr=[make(t) for t in TOPICS];val=[make(t) for t in HOLDOUT]
    # Exclude the holdout topics from replay: exact keyword separation only.
    excluded=("写真","夜景","撮影","カメラ","園芸","ミント","植物","庭","photo","garden","mint")
    background=[]
    if replay_limit:
        for line in replay.read_text(encoding="utf-8").splitlines():
            if not line.strip():continue
            row=json.loads(line)
            if not isinstance(row.get("user"),str) or not isinstance(row.get("assistant"),str):continue
            text=(row["user"]+" "+row["assistant"]).lower()
            if any(w in text for w in excluded):continue
            background.append(row)
        rng.shuffle(background);background=background[:replay_limit]
    train=tr*repeat+background;rng.shuffle(train)
    out.mkdir(parents=True,exist_ok=True)
    for name,rows in (("train",train),("val",val)):
        with (out/f"{name}.jsonl").open("w",encoding="utf-8") as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    report={"train_contrastive_unique":len(tr),"train_rows":len(train),"holdout":len(val),
            "replay_rows":len(background),"repeat":repeat,
            "warning":"Synthetic topic-conditioned examples. Only 2 heldout scenarios; inspect for overfitting."}
    (out/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,default=Path("data/context_conditional_v0223"))
    p.add_argument("--replay",type=Path,default=Path("data/dialogue_generalization_v0212/train.jsonl"))
    p.add_argument("--repeat",type=int,default=60)
    p.add_argument("--replay-limit",type=int,default=3000)
    a=p.parse_args()
    print(json.dumps(build(a.output,a.replay,a.repeat,a.replay_limit),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
