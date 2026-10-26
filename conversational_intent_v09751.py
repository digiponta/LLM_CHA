"""v0.9.7.51: short conversational evaluations and reported actions.

No knowledge promotion or writing to long-term memory. Strictly opt-in
through existing --final-guard path.
"""
from dataclasses import dataclass,asdict
import re

EVALUATIONS={
 "満足":("SATISFACTION","満足できたんだね。良かった。"),
 "美味しかった":("POSITIVE_EVALUATION","美味しかったんだね。"),
 "おいしかった":("POSITIVE_EVALUATION","美味しかったんだね。"),
 "良かった":("POSITIVE_EVALUATION","それは良かったね。"),
 "いまいち":("NEGATIVE_EVALUATION","期待していたほどではなかったんだね。"),
 "微妙だった":("MIXED_EVALUATION","少し物足りなかったんだね。"),
}
ACTIONS={
 "食べた":("EAT","食べたんだね。どんな味だった？"),
 "飲んだ":("DRINK","飲んだんだね。どんな味だった？"),
 "行った":("GO","行ったんだね。どうだった？"),
 "買った":("BUY","買ったんだね。使ってみた？"),
 "見た":("SEE","見たんだね。どうだった？"),
 "聞いた":("HEAR","聞いたんだね。どう感じた？"),
 "読んだ":("READ","読んだんだね。どうだった？"),
 "食べなかった":("EAT","食べなかったんだね。"),
 "飲まなかった":("DRINK","飲まなかったんだね。"),
 "行かなかった":("GO","行かなかったんだね。"),
 "買わなかった":("BUY","買わなかったんだね。"),
 "見なかった":("SEE","見なかったんだね。"),
 "聞かなかった":("HEAR","聞かなかったんだね。"),
 "読まなかった":("READ","読まなかったんだね。"),
}
VERB_RE=re.compile(r"^(?:(?P<object>[^「」『』。！？?!、\n]{1,60}?)(?P<particle>を|へ|に))?(?P<verb>"+("|".join(re.escape(x) for x in sorted(ACTIONS,key=len,reverse=True)))+r")[。！! ]*$")
QUESTION_MARKERS=("？","?","とは","って何","の意味","教えて","ですか","でしょうか")
@dataclass(frozen=True)
class ConversationalIntent:
    intent:str
    action:str|None
    object:str|None
    negated:bool
    response:str
    source:str="USER_UTTERANCE"
    train_ready:bool=False
    auto_promote:bool=False
    persisted:bool=False
    def snapshot(self):return asdict(self)

def detect(text):
    t=str(text or "").strip().rstrip("。！! ")
    if not t or any(q in t for q in QUESTION_MARKERS):return None
    if t in EVALUATIONS:
        intent,response=EVALUATIONS[t]
        return ConversationalIntent(intent,None,None,False,response)
    m=VERB_RE.fullmatch(t)
    if m is None:return None
    verb=m.group("verb")
    action,reply=ACTIONS[verb]
    obj=(m.group("object") or "").strip()
    if len(obj)>45 or "けど" in obj or "けれど" in obj:return None
    if obj:
        # Preserve the user's stated predicate, including negative polarity.
        reply=obj+("を" if m.group("particle")=="を" else m.group("particle"))+verb+"んだね。" if verb.endswith("なかった") else obj+m.group("particle")+verb+"んだね。どうだった？"
    return ConversationalIntent("DAILY_ACTION",action,obj or None,
                                verb.endswith("なかった"),reply)
