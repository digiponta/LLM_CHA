"""v0.2.11 targeted dialogue-transition supervision.

All examples are hand-authored training fixtures, not collected empirical transcripts.
Holdout is topic-disjoint; keep its answers strictly outside the training file.
"""
from __future__ import annotations
import argparse,json,random
from pathlib import Path

TRAIN=[
[("最近、小説にはまっています","どんなジャンルを読んでいるの？"),("SFです","SFなら、宇宙探査や未来社会を描く作品がある。どちらに興味がある？"),("宇宙探査です","宇宙探査を描く作品では、未知の世界への旅や人間の選択がテーマになることが多い。"),("その話、続けて","未知の惑星に着いた探査隊が、限られた情報を基に判断する展開などが考えられる。")],
[("最近は料理をしています","どんな料理を作っているの？"),("パスタです","パスタなら、ソースによって味わいが変わる。トマト系とクリーム系、どちらが好き？"),("トマト系です","トマト系なら、酸味を生かしたシンプルなソースもいい。"),("もっと教えて","にんにくを軽く温めて香りを出し、トマトと合わせる方法がある。")],
[("音楽をよく聴きます","どんな音楽が好き？"),("ジャズです","ジャズには即興演奏の楽しさがある。演奏と歌、どちらをよく聴く？"),("演奏です","楽器同士の掛け合いを聴くと、即興の面白さが伝わってくる。"),("続けて","同じ曲でも演奏者によってフレーズやリズムの取り方が変わる。")],
[("週末は散歩しました","どこを歩いたの？"),("公園です","公園なら、季節の植物や空の変化を楽しめる。何か印象に残った？"),("花です","花を見ると季節の変化を感じられる。色や形にも違いがある。"),("その話を続けて","花の咲く時期や香りを比べると、同じ公園でも新しい発見がある。")],
[("映画を見ました","どんな映画だった？"),("ミステリーです","ミステリーなら、手がかりを集めて推理する過程が面白い。結末は予想できた？"),("予想外でした","意外な結末には、前半の小さな伏線が関係していることもある。"),("もっと聞きたい","伏線が後半で別の意味を持つと、もう一度見返したくなる。")],
[("最近ゲームをしています","どんなジャンルのゲーム？"),("パズルです","パズルなら、少しずつ解法を見つける過程が楽しい。難しいものが好き？"),("はい","難しい問題ほど、解けたときの達成感が大きい。"),("続けて","行き詰まったときに別の角度から見ると、意外な手順が見つかる。")],
]
HOLDOUT=[
[("最近、写真を撮っています","どんな写真を撮るの？"),("夜景です","夜景では光と暗さの対比が魅力になる。街並みと星空、どちらを撮る？"),("街並みです","街の明かりや建物の輪郭に注目すると、場所ごとに違った雰囲気を写せる。"),("その話、続けて","反射する光や人の動きも加えると、同じ夜景でも違った表情になる。")],
[("最近、庭仕事を始めました","何を育てているの？"),("ハーブです","ハーブなら、香りや葉の形を観察する楽しみがある。何の種類？"),("ミントです","ミントは爽やかな香りが特徴で、飲み物にも利用される。"),("続けて","葉を軽く触って香りを確かめると、育ち方の変化を楽しめる。")],
]
def expand(sessions):
    out=[]
    for session in sessions:
        for i,(q,a) in enumerate(session):
            start=max(0,i-2)
            prefix="\n".join(f"人: {user}\nAI: {answer}" for user,answer in session[start:i])
            prompt=(prefix+"\n" if prefix else "")+"人: "+q
            out.append({"user":prompt,"assistant":a})
    return out
def build(output:Path,quality_train:Path,persona:Path,background_limit:int=3000,seed:int=42):
    train=expand(TRAIN);val=expand(HOLDOUT)
    if {r["user"] for r in train} & {r["user"] for r in val}:raise ValueError("train/val leakage")
    output.mkdir(parents=True,exist_ok=True)
    randomizer=random.Random(seed)
    extra=[json.loads(line) for line in quality_train.read_text(encoding="utf-8").splitlines() if line.strip()]
    randomizer.shuffle(extra)
    extra=[r for r in extra if isinstance(r.get("user"),str) and isinstance(r.get("assistant"),str)][:background_limit]
    # Dialogue examples are repeated at controlled small scale while broad replay protects general fluency.
    train=train*30+extra
    randomizer.shuffle(train)
    for name,rows in (("dialogue_train.jsonl",train),("dialogue_val.jsonl",val)):
        with (output/name).open("w",encoding="utf-8") as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    if not persona.is_file():raise FileNotFoundError(persona)
    stats={"train_rows":len(train),"heldout_rows":len(val),"heldout_topics":["night photography","herbs"],"source":"manually authored synthetic dialogues and v028 replay","background_rows":len(extra)}
    (output/"manifest.json").write_text(json.dumps(stats,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return stats
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--quality-train",type=Path,default=Path("data/realpersonachat_quality/quality_train.jsonl"))
    p.add_argument("--persona",type=Path,default=Path("data/realpersonachat_quality/persona_anchors_preformatted.jsonl"))
    p.add_argument("--output",type=Path,default=Path("data/dialogue_sft_v0211"))
    p.add_argument("--background-limit",type=int,default=3000)
    a=p.parse_args()
    print(json.dumps(build(a.output,a.quality_train,a.persona,a.background_limit),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
