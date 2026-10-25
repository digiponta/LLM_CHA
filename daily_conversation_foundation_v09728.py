"""v0.9.7.28 daily conversation foundation: data, labels and leakage audit.

Do not use these examples as an online fallback or automatically train weights.
"""
import json
from collections import Counter

SEEDS={
 "POSITIVE":[("今日は楽しかった","それは良かったね。"),("とても満足した","満足できたのね。良かった。"),("美味しかった","美味しかったんだね。良かった。"),("嬉しいことがあった","それは嬉しいね。"),("うまくできた","うまくいったんだね。")],
 "DISAPPOINTMENT":[("期待外れだった","それは残念だったね。"),("美味しくなかった","それは残念だったね。"),("楽しみにしていたのに中止になった","それは残念だったね。"),("思ったほど良くなかった","期待と違ったんだね。"),("失敗してしまった","それは残念だったね。")],
 "SADNESS":[("悲しかった","それは悲しかったね。"),("寂しい気分だ","寂しいんだね。"),("落ち込んでいる","つらい気持ちなんだね。"),("大切な物をなくした","それはつらかったね。"),("今日は泣いてしまった","悲しいことがあったんだね。")],
 "FATIGUE":[("今日は疲れた","お疲れさま。少し休む？"),("もうへとへとだ","お疲れさま。無理しないでね。"),("眠くなってきた","眠いんだね。休めそう？"),("一日中忙しかった","忙しい一日だったんだね。"),("少し休みたい","うん、少し休もう。")],
 "GRATITUDE":[("ありがとう","どういたしまして。"),("助かったよ","役に立てて良かった。"),("感謝している","そう言ってもらえて嬉しい。"),("どうもありがとう","どういたしまして。"),("手伝ってくれてありがとう","どういたしまして。")],
 "UNCERTAINTY":[("どうしたらいいか分からない","何に困っているの？"),("少し迷っている","どのあたりで迷っているの？"),("決められない","選択肢を一緒に整理しようか。"),("困っている","何か手伝えることはある？"),("よく分からない","どの部分が分からない？")],
}
# Intentionally distinct wording; never select these for training.
HOLDOUT={
 "POSITIVE":[("思いがけず楽しい一日だった","良い一日だったんだね。"),("すごく気に入った","気に入ったんだね。良かった。")],
 "DISAPPOINTMENT":[("思っていたのと違ってがっかりした","それは残念だったね。"),("せっかく行ったのに楽しめなかった","期待していたなら残念だね。")],
 "SADNESS":[("何だかしんみりしている","少し寂しい気分なんだね。"),("悲しくて元気が出ない","つらいんだね。")],
 "FATIGUE":[("今日はくたくただ","お疲れさま。休めるといいね。"),("集中しすぎて疲れた","頑張ったんだね。少し休む？")],
 "GRATITUDE":[("お礼を言いたかった","どういたしまして。"),("本当に助かった","役に立てて良かった。")],
 "UNCERTAINTY":[("判断に悩んでいる","何が気になっているの？"),("どちらがいいか迷う","一緒に比べてみようか。")],
}
STRATEGIES={
 "POSITIVE":"POSITIVE_ACKNOWLEDGEMENT",
 "DISAPPOINTMENT":"SYMPATHETIC_ACKNOWLEDGEMENT",
 "SADNESS":"EMOTIONAL_VALIDATION",
 "FATIGUE":"REST_SUPPORT",
 "GRATITUDE":"GRATITUDE_REPLY",
 "UNCERTAINTY":"CLARIFY_OR_SUPPORT",
}
def records(groups,split):
    return [{"id":f"{split}-{label}-{idx:02d}","split":split,"input":utterance,
             "semantic":{"dialogue_act":"SHARE_EXPERIENCE" if label not in ("GRATITUDE","UNCERTAINTY") else ("EXPRESS_GRATITUDE" if label=="GRATITUDE" else "REQUEST_SUPPORT"),
                         "emotion":label,"response_strategy":STRATEGIES[label]},
             "target":reply,"provenance":"CURATED_SYNTHETIC"}
             for label,pairs in groups.items() for idx,(utterance,reply) in enumerate(pairs,1)]
def dataset():
    return {"schema":"daily-conversation-foundation-v0.1",
            "train":records(SEEDS,"train"),"holdout":records(HOLDOUT,"holdout"),
            "auto_promote":False,"train_ready":False}
def audit(data=None):
    d=data or dataset()
    train=d["train"];holdout=d["holdout"]
    inputs=[r["input"] for r in train+holdout]
    duplicate=len(inputs)-len(set(inputs))
    overlap=set(r["input"] for r in train)&set(r["input"] for r in holdout)
    counts={part:dict(Counter(r["semantic"]["emotion"] for r in d[part]))
            for part in ("train","holdout")}
    return {"train_count":len(train),"holdout_count":len(holdout),
            "counts":counts,"exact_duplicate_count":duplicate,
            "train_holdout_overlap":sorted(overlap),
            "ready_for_controlled_training":not duplicate and not overlap,
            "note":"Synthetic curated baseline; real dialogue generalization untested"}
if __name__=="__main__":
    print(json.dumps(audit(),ensure_ascii=False,indent=2))
