"""LLM_CHA v0.2.31.0: deterministic Purpose Discovery Dialogue prototype.

A separate controller, not a claim that the LM acquired purpose reasoning.
It asks one question per turn and preserves a structured dialogue state.
"""
from dataclasses import dataclass,field,asdict
import re,json

STATES=("UNKNOWN","DISCOVERING","CONFIRMING","READY","EXECUTING")
TOPICS=("Python","AI","LLM","画像認識")
PURPOSES=("learning","development","troubleshooting","casual")
PURPOSE_LABEL={"learning":"学習","development":"開発","troubleshooting":"エラー解決","casual":"雑談"}

@dataclass
class DialogueSemanticState:
    state:str="UNKNOWN"
    topic:str|None=None
    purpose:str|None=None
    candidates:list[str]=field(default_factory=list)
    missing:list[str]=field(default_factory=lambda:["user_goal"])
    next_action:str="ASK_CLARIFICATION"
    turns:int=0
    last_question:str|None=None

def infer_topic(text):
    for topic in ("画像認識","LLM","Python","AI"):
        if topic.lower() in text.lower():return topic
    return None

def infer_purpose(text):
    if re.search(r"雑談|少し話|おしゃべり|話し相手",text):return "casual"
    if re.search(r"エラー|直したい|動かない|不具合|例外",text):return "troubleshooting"
    if re.search(r"自作|作りたい|開発したい|実装したい|構築したい",text):return "development"
    if re.search(r"学習したい|勉強したい|使い方|教えて|知りたい",text):return "learning"
    return None

def explicit_switch(text):
    return bool(re.search(r"やっぱり|それより|代わりに|変更したい|話題を変え",text))

def next_question(dss):
    if dss.topic in ("Python","AI"):
        return f"{dss.topic}について、学習したいですか、それとも何か作りたいですか？"
    if dss.topic:
        return f"{dss.topic}について、何をしたいですか？"
    return "どんなことをしたいですか？ 雑談でも構いません。"

def respond(dss,text):
    """Return (updated DSS, action, response). One direct question maximum."""
    text=text.strip()
    if not text:return dss,"ASK_CLARIFICATION","何について話しましょうか？"
    if dss.state not in STATES:raise ValueError("unknown dialogue state")
    dss.turns+=1
    new_topic=infer_topic(text)
    goal=infer_purpose(text)
    changing=explicit_switch(text)
    # Explicit goal change takes precedence over previous status.
    if changing and (new_topic or goal):
        dss.topic=new_topic or dss.topic
        dss.purpose=goal
        dss.candidates=[]
        dss.state="DISCOVERING"
    elif new_topic:
        dss.topic=new_topic
    if goal:
        dss.purpose=goal
    # "AIを作りたい" still lacks artifact specification, unless a target
    # like LLM or image recognition was named.
    needs_target=dss.purpose=="development" and dss.topic in ("AI",None)
    if needs_target:
        dss.state="DISCOVERING"
        dss.candidates=["LLM","画像認識","その他のAI"]
        dss.missing=["development_target"]
        dss.next_action="ASK_CLARIFICATION"
        question="どんなAIを作りたいですか？ 会話用LLM、画像認識、それとも別の種類ですか？"
        dss.last_question=question
        return dss,dss.next_action,question
    if dss.purpose is None:
        dss.state="DISCOVERING" if dss.topic else "UNKNOWN"
        dss.candidates=list(PURPOSES)
        dss.missing=["user_goal"]
        dss.next_action="ASK_CLARIFICATION"
        question=next_question(dss)
        if question==dss.last_question:
            question="学習、開発、エラー解決、雑談のうち、今の希望に近いものはありますか？"
        dss.last_question=question
        return dss,dss.next_action,question
    dss.candidates=[]
    dss.missing=[]
    dss.state="READY"
    dss.next_action="RESPOND"
    if dss.purpose=="casual":
        dss.state="EXECUTING"
        return dss,"RESPOND","もちろんです。最近、気になっていることはありますか？"
    if dss.topic is None:
        dss.state="DISCOVERING"
        dss.missing=["topic"]
        dss.next_action="ASK_CLARIFICATION"
        dss.last_question="何について進めたいですか？"
        return dss,dss.next_action,dss.last_question
    dss.state="EXECUTING"
    # Planner handoff instead of unverified LLM prose generation.
    return dss,"HANDOFF",f"{dss.topic}の{PURPOSE_LABEL[dss.purpose]}を目的として受け付けました。次に具体的な内容を進めます。"

def snapshot(dss):
    return asdict(dss)

def main():
    dss=DialogueSemanticState()
    print("LLM_CHA Purpose Discovery Dialogue v0.2.31.0")
    print("Commands: /state /reset /quit")
    while True:
        try:text=input("You> ")
        except (EOFError,KeyboardInterrupt):break
        if text.strip()=="/quit":break
        if text.strip()=="/state":
            print(json.dumps(snapshot(dss),ensure_ascii=False,indent=2));continue
        if text.strip()=="/reset":
            dss=DialogueSemanticState();print("DSS reset");continue
        dss,action,message=respond(dss,text)
        print(f"CHA[{dss.state}/{action}]> {message}")
if __name__=="__main__":main()
