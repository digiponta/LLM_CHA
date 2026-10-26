"""Conservative final-answer diagnostics and daily-intent guard for LLM_CHA.

Only high-precision probes. Unknown content is REVIEW, not certified.
"""
from dataclasses import dataclass,asdict
import re

BROKEN=("長門有希丘陵","瀬料水産基地","曼し","疲しい","�")
FOOD=("バゲットサンド","サンドイッチ","ケーキ","パイ","スコーン","パン")
DRINK=("ラテ","コーヒー","フラペチーノ","ジュース","紅茶")
SATISFACTION=re.compile(r"^(?:そう[、， ]*)?(?:満足(?:した|できた|だ|です|だった|している)|(?:とても|すごく)?満足したよ)[。！! ]*$")
SEMANTIC_REPLIES={
 "満足":"満足できたんだね。良かった。",
}

@dataclass(frozen=True)
class FinalDecision:
    decision:str
    reason:str
    original:str
    selected:str
    route:str
    train_ready:bool=False
    auto_promote:bool=False
    persisted:bool=False
    def snapshot(self):return asdict(self)

def daily_intent(text):
    t=str(text or "").strip()
    if SATISFACTION.fullmatch(t):
        return FinalDecision("HANDLE","daily-satisfaction","",
                             SEMANTIC_REPLIES["満足"],"DAILY_SATISFACTION")
    return None

def inspect_answer(user_text,answer,route="MODEL_GENERATION"):
    u=str(user_text or "").strip()
    a=str(answer or "").strip()
    if not a or any(w in a for w in BROKEN):
        return FinalDecision("REJECT","malformed-or-known-collapse",a,
             "うまく答えられなかった。もう一度、別の言い方で聞いてもらえる？",
             route)
    if any(w in a for w in FOOD) and "飲んだ" in a and not any(w in a for w in DRINK):
        return FinalDecision("REJECT","food-drink-verb-conflict",a,
                             a.replace("を飲んだ","を食べた"),route)
    if len(a)>250:
        return FinalDecision("REVIEW","long-answer-not-verified",a,a,route)
    return FinalDecision("REVIEW","not-independently-verified",a,a,route)
