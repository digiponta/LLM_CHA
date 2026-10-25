"""Semantic-aware daily conversation data v0.9.7.32.

Do not reuse v0.9.7.28 holdout inputs for gradient updates.
Negation and mixed-emotion cases preserve explicit response strategies.
"""
import json
from daily_conversation_foundation_v09728 import dataset as legacy

TRAIN={
"POSITIVE":[("今日は最高の気分だった","それは良かったね。"),("思った以上に楽しめた","楽しめたんだね。良かった。"),("飲み物がとても気に入った","気に入ったんだね。良かった。"),("うれしい知らせが来た","それは嬉しいね。"),("満ち足りた気持ちだ","満足できたんだね。良かった。")],
"DISAPPOINTMENT":[("予定がなくなってがっかりだ","それは残念だったね。"),("購入した品は期待ほどではなかった","期待外れだったんだね。"),("楽しみだったのに失敗した","それは残念だったね。"),("想像よりも味が悪かった","それは残念だったね。"),("今回の結果は不満だ","思い通りにならなかったんだね。")],
"SADNESS":[("今日は気持ちが沈んでいる","つらい気分なんだね。"),("寂しさを感じた","寂しかったんだね。"),("別れが悲しい","それは悲しいね。"),("涙が出そうだ","つらいことがあったんだね。"),("心細かった","心細かったんだね。")],
"FATIGUE":[("一日歩いて疲労した","お疲れさま。少し休む？"),("仕事で消耗した","お疲れさま。無理しないでね。"),("もう休息が必要だ","少し休めるといいね。"),("身体がだるい","疲れているんだね。"),("今日は力を使い切った","頑張ったんだね。休めそう？")],
"GRATITUDE":[("感謝の気持ちを伝えたい","どういたしまして。"),("説明が役に立ったよ","役に立てて良かった。"),("助けてくれて感謝する","どういたしまして。"),("手助けがありがたかった","役に立てて良かった。"),("親切にしてくれてありがとう","どういたしまして。")],
"UNCERTAINTY":[("選択に迷いがある","どのあたりで迷っているの？"),("判断が難しい","一緒に整理しようか。"),("どうするべきか悩む","何が気になっているの？"),("選択肢が多くて決まらない","一緒に比べてみようか。"),("何から始めるべきか分からない","最初の一歩を一緒に考えようか。")],
"NEGATED_POSITIVE":[("今日は楽しくなかった","それは残念だったね。"),("飲み物は美味しくなかった","それは残念だったね。"),("期待したけど良くなかった","期待外れだったんだね。"),("気に入らなかった","それは残念だったね。")],
"NEGATED_SADNESS":[("今日は悲しくなかった","悲しくなかったんだね。"),("別に寂しくはなかった","寂しくはなかったんだね。"),("落ち込んでいない","落ち込んではいないんだね。"),("つらくはなかった","つらくはなかったんだね。")],
"MIXED":[("楽しかったけど疲れた","楽しかった一方で、疲れたんだね。"),("嬉しいけれど少し不安だ","嬉しい気持ちも不安もあるんだね。"),("美味しかったけれど高かった","美味しかったけれど値段が気になったんだね。"),("残念だったけど勉強になった","残念だった一方で学びもあったんだね。"),("疲れたけど達成感がある","疲れたけれど達成感もあるんだね。")],
}
EVAL={
"POSITIVE":[("予想外に良い出来事があった","それは良かったね。"),("大満足の一日だった","満足できたんだね。良かった。")],
"DISAPPOINTMENT":[("楽しみにしていた企画が期待外れだ","それは残念だったね。"),("結果にがっかりしている","期待と違ったんだね。")],
"SADNESS":[("切ない気持ちになった","切ない気分なんだね。"),("今日はどうも気分が沈む","つらい気分なんだね。")],
"FATIGUE":[("今日はぐったりしている","お疲れさま。少し休む？"),("忙しすぎてへばった","お疲れさま。休めそう？")],
"GRATITUDE":[("おかげで救われたよ","役に立てて良かった。"),("お礼を伝えられて良かった","そう言ってもらえて嬉しい。")],
"UNCERTAINTY":[("結論を出せずにいる","どの部分で迷っているの？"),("決断の仕方が分からない","一緒に選択肢を整理しようか。")],
"NEGATED_POSITIVE":[("外出したけれど楽しめなかった","それは残念だったね。"),("まったく気に入らなかった","それは残念だったね。")],
"NEGATED_SADNESS":[("悲しいわけではない","悲しいということではないんだね。"),("寂しくなんてないよ","寂しくはないんだね。")],
"MIXED":[("よかった面もあるけど後悔も残る","良かった面と後悔の両方があるんだね。"),("嬉しいのに少し悲しい","嬉しさと悲しさが重なっているんだね。")],
}
def pack(groups,split):
    return [{"id":f"{split}-{label}-{i:02d}","split":split,
       "input":q,"target":a,"semantic":{"dialogue_act":"SHARE_EXPERIENCE",
       "emotion":label,"response_strategy":"ACKNOWLEDGE_"+label},
       "provenance":"CURATED_SYNTHETIC"} for label,pairs in groups.items()
       for i,(q,a) in enumerate(pairs,1)]
def build():
    older=legacy()
    train=older["train"]+pack(TRAIN,"train")
    # Original holdout is NEVER included in training, and stays evaluation-only.
    holdout=older["holdout"]+pack(EVAL,"holdout")
    train_set={x["input"] for x in train}
    eval_set={x["input"] for x in holdout}
    overlap=train_set&eval_set
    duplicate=len(train)-len(train_set)
    if overlap or duplicate:raise ValueError(f"leakage or duplicates: {overlap}")
    return {"schema":"semantic-daily-dialogue-v0.2",
            "train":train,"holdout":holdout,
            "original_holdout_preserved":True,
            "holdout_used_for_training":False,
            "train_ready":False}
def audit():
    d=build()
    return {"train_count":len(d["train"]),"holdout_count":len(d["holdout"]),
            "categories":sorted({r["semantic"]["emotion"] for r in d["train"]}),
            "train_holdout_overlap":[],
            "original_holdout_preserved":True,
            "holdout_used_for_training":False}
if __name__=="__main__":
    print(json.dumps(audit(),ensure_ascii=False,indent=2))
