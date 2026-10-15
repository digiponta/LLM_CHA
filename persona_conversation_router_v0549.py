"""v0.5.49: conservative conversational sharing route.

This route responds to an explicit, non-question personal activity report.
It does not assert facts about the named subject or alter semantic memory.
"""
import re
from unified_persona_controller_v0548 import persona_for

ARTICLE=re.compile(r"^(?:今日は[、, ]*)?(?P<topic>[^。！？!?]{1,35}?)の(?:記事|ニュース)を(?:読んだ|見た|読んでいた)[。！! ]*$")
DAILY=re.compile(r"^(?:今日は[、, ]*)?(?P<activity>散歩した|散歩に行った|本を読んだ|映画を見た|少し疲れた)[。！! ]*$")
def classify(user):
    if not isinstance(user,str):return {"intent":"OTHER"}
    q=user.strip()
    if not q or q.startswith("/") or any(x in q for x in ("？","?","教えて","とは","なぜ","どう","何","説明して")):
        return {"intent":"OTHER"}
    a=ARTICLE.fullmatch(q)
    if a:
        topic=a.group("topic").strip(" 、")
        if not topic:return {"intent":"OTHER"}
        return {"intent":"ARTICLE_SHARING","topic":topic}
    d=DAILY.fullmatch(q)
    if d:return {"intent":"DAILY_SHARING","activity":d.group("activity")}
    return {"intent":"OTHER"}

def respond(user,persona="nagato"):
    data=classify(user)
    intent=data["intent"]
    if intent=="OTHER":return None
    p=persona_for(persona)
    if intent=="ARTICLE_SHARING":
        topic=data["topic"]
        answer=(f"そう。{topic}の記事を読んだのね。どんな内容だった？"
                if p=="nagato" else
                f"{topic}の記事を読まれたのですね。どんな内容でしたか？")
    else:
        activity=data["activity"]
        answer=(f"そう。{activity}のね。どんな一日だった？"
                if p=="nagato" else
                f"そうだったのですね。{activity}のですね。今日はどんな一日でしたか？")
    return {"answer":answer,"route":"PERSONA_CONVERSATION_SHARING",
      "persona":p,"intent":intent,"knowledge_asserted":False,
      "verified":False,"train_ready":False,"auto_lookup":False,"auto_promote":False}
