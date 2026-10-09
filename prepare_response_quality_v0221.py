"""v0.2.21 context-aware answer SFT, intentionally small and auditable.

All scenario data is manually written; holdout topics never enter training.
"""
from __future__ import annotations
import argparse,json,random
from pathlib import Path
from prepare_dialogue_sft_v0211 import expand

TRAIN=[
[("最近、SF小説を読んでいます","SF小説なんだ。どんな作品を読んでいるの？"),("宇宙探査がテーマです","宇宙探査なら、未知の星を調べる展開が面白そう。主人公の判断に注目している？"),("そうです","限られた情報で決断する場面には緊張感があるね。"),("その話を続けて","宇宙探査の物語では、通信が途絶えたときの選択や仲間との協力が大きな見どころになりそう。")],
[("最近、歴史小説を読んでいます","歴史小説なんだ。どの時代の物語？"),("江戸時代です","江戸時代なら町の暮らしや人間関係を描く作品もあるね。何が面白い？"),("登場人物の関係です","立場や価値観の違いが人物同士の選択に表れそうだね。"),("その話を続けて","同じ事件を別の人物の視点から見ると、関係の変化がよりはっきり伝わることがある。")],
[("週末は山を歩きました","山歩きなんだ。景色と道のり、どちらが印象に残った？"),("景色です","どんな景色だった？ 山の上からの眺めかな。"),("雲海でした","雲海が見えたんだね。雲の広がりは印象的だったと思う。"),("もっと聞かせて","雲が谷を覆うと、山の稜線だけが浮かぶように見えることがある。")],
[("最近、音楽を聴いています","音楽を聴いているんだ。どんなジャンル？"),("クラシックです","クラシックなんだ。管弦楽とピアノ曲ならどちらを聴く？"),("ピアノ曲です","ピアノ曲は音の強弱で雰囲気が変わるね。好きな演奏はある？"),("続きを話して","同じ曲でも弾く速さや間の取り方が違うと、聞こえ方が大きく変わる。")],
[("今日は料理をしました","何を作ったの？"),("カレーです","カレーなんだ。辛さや具材にはこだわりがある？"),("野菜を多くしました","野菜が多いと食感も豊かになるね。どんな野菜を入れたの？"),("その話を続けて","火の通りにくい野菜から煮ると、具材ごとの食感を調整しやすい。")],
[("最近、プログラミングをしています","何を作っているの？"),("小さなゲームです","ゲームなんだ。操作とルールのどちらを工夫している？"),("ルールです","ルール次第で遊び方が変わるね。どんな仕組みを考えている？"),("続きを教えて","最初は単純なルールにして、遊びながら要素を一つずつ追加すると変化を確かめやすい。")],
]
HOLDOUT=[
[("最近、写真を撮っています","写真を撮っているんだ。どんな被写体が好き？"),("夜景です","夜景なら街の光がきれいに写るね。どんな場所で撮るの？"),("川沿いです","川に映る明かりも楽しめそう。"),("その話を続けて","水面の反射が揺れると、街の光が線のように見えることもある。")],
[("最近、庭で植物を育てています","何を育てているの？"),("ミントです","ミントなんだ。香りを楽しむために育てている？"),("そうです","葉の香りが変わる様子を観察するのも面白いね。"),("続きを話して","葉を少し触って香りを確かめると、成長に伴う変化が分かりやすい。")],
]
def build(output:Path,replay:Path,replay_limit=4000,repeat=12,seed=42):
    if repeat<1 or replay_limit<0:raise ValueError("repeat/replay_limit invalid")
    tr=expand(TRAIN);val=expand(HOLDOUT)
    assert not ({x["user"] for x in tr}&{x["user"] for x in val})
    # Explicit holdout-topic exclusion in broad replay: avoid using
    # photos/gardens and a proxy for lexical leakage.
    forbidden=("写真","夜景","撮影","カメラ","庭","植物","ミント","園芸","ハーブ","photo","garden","mint")
    rng=random.Random(seed)
    background=[]
    if replay_limit:
        for line in replay.read_text(encoding="utf-8").splitlines():
            if not line.strip():continue
            row=json.loads(line)
            if not isinstance(row.get("user"),str) or not isinstance(row.get("assistant"),str):continue
            combined=(row["user"]+" "+row["assistant"]).lower()
            if any(term in combined for term in forbidden):continue
            background.append({"user":row["user"],"assistant":row["assistant"]})
        rng.shuffle(background);background=background[:replay_limit]
    train=tr*repeat+background;rng.shuffle(train)
    output.mkdir(parents=True,exist_ok=True)
    for name,rows in (("train.jsonl",train),("val.jsonl",val)):
        with (output/name).open("w",encoding="utf-8") as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    manifest={"synthetic_train_unique":len(tr),"synthetic_holdout":len(val),"repeat":repeat,
              "replay_rows":len(background),"train_rows":len(train),"holdout_topics":["photo","garden"],
              "seed":seed,"note":"hand-authored synthetic SFT; broad replay from preexisting training split only"}
    (output/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,default=Path("data/response_quality_v021"))
    p.add_argument("--replay",type=Path,default=Path("data/dialogue_generalization_v0212/train.jsonl"))
    p.add_argument("--replay-limit",type=int,default=4000)
    p.add_argument("--repeat",type=int,default=12)
    a=p.parse_args();print(json.dumps(build(a.output,a.replay,a.replay_limit,a.repeat),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
