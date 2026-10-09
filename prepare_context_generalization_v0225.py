"""v0.2.25: diversified context SFT, topic-disjoint holdout."""
from __future__ import annotations
import argparse,json,random
from pathlib import Path

TRAIN=[
("SF小説","宇宙探査","宇宙探査の物語では、未知の惑星や乗組員の選択が見どころになるね。"),
("料理","カレー","カレーなら、野菜や香辛料の組み合わせで味の変化を楽しめるね。"),
("音楽","クラシック","クラシック音楽では、楽器の音色や演奏によって印象が変わるね。"),
("散歩","公園","公園を歩くと、季節の花や木々の変化に気づけるね。"),
("プログラミング","ゲーム","ゲーム開発では、ルールを少し変えるだけで遊び方が変わるね。"),
("読書","歴史小説","歴史小説では、時代背景と登場人物の関係が物語を深くするね。"),
("運動","水泳","水泳では、呼吸のリズムや泳ぎ方を工夫すると楽しみが広がるね。"),
("旅行","鉄道","鉄道旅行では、車窓から見える景色や駅ごとの雰囲気を味わえるね。"),
("映画","ミステリー","ミステリー映画では、小さな伏線が結末につながる展開が面白いね。"),
("科学","天文学","天文学では、星や銀河の観測から宇宙のしくみを探れるね。"),
("絵画","水彩画","水彩画では、色の重なりや水の量で表現が変わるね。"),
("工作","模型","模型作りでは、細部の組み立てと完成までの工夫が楽しいね。"),
("読書","推理小説","推理小説では、登場人物の言葉や行動が手がかりになるね。"),
("食事","和食","和食では、旬の食材やだしの風味を楽しめるね。"),
("スポーツ","テニス","テニスでは、ラリーの駆け引きやコースの選び方が面白いね。"),
("手芸","編み物","編み物は、糸の色や編み方によって仕上がりが変わるね。"),
("学習","外国語","外国語の学習では、短い会話を繰り返すと表現が身についていくね。"),
("ゲーム","パズル","パズルでは、見方を変えると解法が見つかることがあるね。"),
]
HOLDOUT=[
("写真","夜景","夜景撮影では、水面の反射や街の明かりを生かせるね。"),
("園芸","ミント","ミントの栽培では、葉の香りや成長の変化を観察できるね。"),
("天気","雨雲","雨雲を見ると、空の色や雲の動きの変化に気づくね。"),
("ペット","猫","猫との暮らしでは、しぐさや表情から気分を感じ取れるね。"),
("乗り物","自転車","自転車で走ると、道沿いの景色を近くに感じられるね。"),
("文化","陶芸","陶芸では、土の感触や釉薬の色の変化を楽しめるね。"),
]
def make(t):
    theme,focus,answer=t
    return {"user":f"人: 最近、{theme}に興味があります\nAI: どんなことに興味があるの？\n人: {focus}です\nAI: その話を聞かせて\n人: その話を続けて","assistant":answer}
def write(path,rows):
    with path.open("w",encoding="utf-8") as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
def build(output,replay,weight=12,replay_limit=3000,seed=42):
    if weight<1 or replay_limit<2:raise ValueError("invalid weight/replay limit")
    train=[make(t) for t in TRAIN];hold=[make(t) for t in HOLDOUT]
    excluded=tuple(x.lower() for t in HOLDOUT for x in t[:2])+("写真","撮影","カメラ","園芸","植物","庭","photo","garden","weather","cat","bicycle","pottery")
    rows=[]
    for s in replay.read_text(encoding="utf-8").splitlines():
        if not s.strip():continue
        row=json.loads(s)
        if not isinstance(row.get("user"),str) or not isinstance(row.get("assistant"),str):continue
        if any(x in (row["user"]+" "+row["assistant"]).lower() for x in excluded):continue
        rows.append(row)
    rng=random.Random(seed);rng.shuffle(rows)
    seen=set();replay_rows=[]
    for row in rows:
        k=(row["user"],row["assistant"])
        if k in seen:continue
        seen.add(k);replay_rows.append(row)
        if len(replay_rows)>=replay_limit:break
    if len(replay_rows)<2:raise ValueError("too few replay examples")
    output.mkdir(parents=True,exist_ok=True)
    write(output/"train.jsonl",replay_rows);write(output/"context.jsonl",train);write(output/"val.jsonl",hold)
    m={"unique_context_pairs":len(train),"context_weight":weight,"context_exposures":len(train)*weight,"replay_pairs":len(replay_rows),"holdout_pairs":len(hold),"seed":seed,
       "note":"Synthetic 18-topic pilot, 6 disjoint holdouts; inspect overlap manually"}
    (output/"manifest.json").write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return m
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,default=Path("data/context_generalization_v0225"))
    p.add_argument("--replay",type=Path,default=Path("data/dialogue_generalization_v0212/train.jsonl"))
    p.add_argument("--weight",type=int,default=12);p.add_argument("--replay-limit",type=int,default=3000)
    a=p.parse_args()
    print(json.dumps(build(a.output,a.replay,a.weight,a.replay_limit),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
