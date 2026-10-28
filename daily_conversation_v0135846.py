"""LLM_CHA v0.13.58.46: limited opt-in daily conversation support.

Intent rules are deliberately narrow. No claims of model generalization or SFT.
Factual questions, slash commands, and ambiguous inputs return None to legacy chat.
"""
import os,re
from dataclasses import dataclass

@dataclass(frozen=True)
class DailyReply:
    intent: str
    answer: str

_RULES = (
    ("greeting", re.compile(r"^(?:こんにちは|こんばんは|おはよう(?:ございます)?)[！!。.\s]*$"), "こんにちは。今日は何について話そうか。"),
    ("thanks", re.compile(r"^(?:ありがとう|どうもありがとう|助かった(?:、?ありがとう)?)[！!。.\s]*$"), "どういたしまして。"),
    ("feeling_tired", re.compile(r"^(?:今日は|ちょっと|少し|なんだか|最近)?(?:疲れた|疲れ気味|眠い|眠くなってきた)[！!。.\s]*$"), "そうなんだ。無理をせず、少し休むのもいいと思う。"),
    ("feeling_good", re.compile(r"^(?:今日は|なんだか|ちょっと)?(?:いい気分|気分がいい|うれしい)[！!。.\s]*$"), "それはいいね。何かうれしいことがあった？"),
    ("casual_invite", re.compile(r"^(?:少し|ちょっと)?(?:話そう|話さない[？?]?|おしゃべりしよう)[！!。.\s]*$"), "いいよ。最近気になっていることはある？"),
)
def classify(question):
    q=question.strip()
    if not q or q.startswith("/") or len(q)>80 or "\n" in q:
        return None
    matches=[DailyReply(intent,answer) for intent,pat,answer in _RULES if pat.fullmatch(q)]
    return matches[0] if len(matches)==1 else None

def route(question,env=None):
    env=os.environ if env is None else env
    if env.get("LLM_CHA_DAILY_RUNTIME")!="1":
        return None
    return classify(question)
