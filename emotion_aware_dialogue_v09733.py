"""Conservative, inspectable emotion-aware dialogue v0.9.7.33.

Rule-based reference baseline, NOT a trained emotion classifier. It handles
clear first-person emotions and dialogue acts, and abstains on uncertainty.
"""
from dataclasses import dataclass, asdict
import re

RULES={
 "JOY": ("嬉しい","うれしい","合格した","成功した","達成した","やった","満足した"),
 "ENJOYMENT": ("楽しかった","楽しい","楽しめた","面白かった","気に入った"),
 "ANGER": ("腹が立つ","むかつく","怒っている","理不尽","許せない"),
 "SADNESS": ("悲しい","悲しかった","寂しい","寂しかった","つらい","辛い","落ち込んだ"),
 "DISAPPOINTMENT": ("残念","がっかり","期待外れ","楽しめなかった","楽しくなかった","美味しくなかった","気に入らなかった"),
 "FATIGUE": ("疲れた","くたくた","ぐったり","へとへと"),
 "GRATITUDE": ("ありがとう","感謝","助かった","お礼"),
 "UNCERTAINTY": ("迷っている","迷う","悩んでいる","判断が難しい","決められない"),
}
NEGATED={
 "悲しくない":"SADNESS","悲しくなかった":"SADNESS",
 "悲しいわけではない":"SADNESS","寂しくない":"SADNESS",
 "寂しくはなかった":"SADNESS","落ち込んでいない":"SADNESS",
 "つらくはなかった":"SADNESS","辛くない":"SADNESS",
}
GREETINGS={"こんにちは","こんばんは","おはよう","おはようございます"}
STRATEGIES={
 "JOY":("CELEBRATE","それは嬉しい知らせだね。"),
 "ENJOYMENT":("SHARE_JOY","楽しかったんだね。良かった。"),
 "ANGER":("VALIDATE_FEELING","それは腹が立つよね。"),
 "SADNESS":("EMPATHIZE","それはつらかったね。"),
 "DISAPPOINTMENT":("ACKNOWLEDGE_DISAPPOINTMENT","それは残念だったね。"),
 "FATIGUE":("CARE","お疲れさま。少し休めるといいね。"),
 "GRATITUDE":("ACKNOWLEDGE_THANKS","どういたしまして。"),
 "UNCERTAINTY":("CLARIFY","どのあたりで迷っているの？"),
 "NON_SADNESS":("ACKNOWLEDGE_NEGATION","悲しいわけではないんだね。"),
 "MIXED":("ACKNOWLEDGE_BOTH","いろいろな気持ちが重なっているんだね。"),
 "GREETING":("GREET","こんにちは。今日はどうしたの？"),
}
@dataclass(frozen=True)
class EmotionDecision:
    dialogue_act:str
    primary:str
    secondary:tuple
    strategy:str
    response:str
    reason:str
    confident:bool
    provenance:str="USER_UTTERANCE"
    train_ready:bool=False
    auto_promote:bool=False
    persisted:bool=False
    def snapshot(self):return asdict(self)

def detect(text):
    q=str(text or "").strip().rstrip("。！! ")
    if not q or q.startswith("/"):return None
    if q.endswith(("?","？")):return None
    if q in GREETINGS:
        strategy,response=STRATEGIES["GREETING"]
        return EmotionDecision("GREETING","NEUTRAL",(),strategy,response,"explicit-greeting",True)
    if "誰" in q or "何" in q and "ですか" in q:return None
    # First resolve explicit negation before looking for positive/negative stems.
    for phrase,underlying in NEGATED.items():
        if phrase in q:
            strategy,response=STRATEGIES["NON_SADNESS"]
            return EmotionDecision("EMOTION_REPORT","NON_SADNESS",(),strategy,response,"explicit-negation:"+underlying,True)
    matched=[label for label,words in RULES.items() if any(w in q for w in words)]
    # A non-specific phrase can contain conflicting terms. Do not guess.
    if len(matched)>1:
        # Mixed response only for an explicit conjunction, never for mere cooccurrence.
        if any(w in q for w in ("けど","けれど","一方","なのに")):
            strategy,response=STRATEGIES["MIXED"]
            return EmotionDecision("EMOTION_REPORT","MIXED",tuple(matched),strategy,response,"explicit-contrast",True)
        return None
    if not matched:return None
    label=matched[0]
    strategy,response=STRATEGIES[label]
    return EmotionDecision("EMOTION_REPORT",label,(),strategy,response,"explicit-emotion",True)

class EmotionDialogue:
    def __init__(self):self.last=None
    def reset(self):self.last=None
    def respond(self,utterance):
        decision=detect(utterance)
        self.last=decision
        return decision.response if decision and decision.confident else None
    def snapshot(self):
        return self.last.snapshot() if self.last else {"status":"NO_CONFIDENT_EMOTION",
          "train_ready":False,"auto_promote":False,"persisted":False}
