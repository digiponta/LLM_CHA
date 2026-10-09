"""v0.2.31.1: purpose confidence and explicit confirmation controller.

Standalone deterministic baseline; it does not train an LLM. Do not treat
heuristic confidence as a calibrated probability.
"""
from dataclasses import dataclass,field,asdict
import re,json

LABELS={"learning":"学習","development":"開発","troubleshooting":"エラー解決","casual":"雑談"}
STATES={"UNKNOWN","DISCOVERING","CONFIRMING","READY","EXECUTING"}
TOPIC_PATTERN=("画像認識","LLM","Python","AI")
INTENT_PATTERNS=(
 ("casual",r"雑談|おしゃべり|話し相手|少し話"),
 ("troubleshooting",r"エラー|不具合|例外|動かない|修正したい"),
 ("development",r"自作したい|作りたい|開発したい|実装したい|構築したい"),
 ("learning",r"学習したい|勉強したい|使い方|教えて|知りたい"),
)
AMBIGUOUS=r"試したい|触ってみたい|何かしたい|興味がある|やってみたい"
YES=r"^(はい|うん|そうです|その通り|それで|お願いします|正解|yes|y)[。！! ]*$"
NO=r"^(いいえ|違います|違う|いや|そうじゃない|no|n)[。！! ]*$"
SWITCH=r"やっぱり|それより|代わりに|変更したい|話題を変え"

@dataclass
class DSS:
    state:str="UNKNOWN"
    topic:str|None=None
    purpose:str|None=None
    confidence:float=0.0
    confidence_kind:str="heuristic_not_calibrated"
    candidate_purpose:str|None=None
    candidates:list[str]=field(default_factory=list)
    missing:list[str]=field(default_factory=lambda:["user_goal"])
    next_action:str="ASK_CLARIFICATION"
    last_question:str|None=None
    last_rejected_purpose:str|None=None
    turns:int=0

def topic_of(text):
    for topic in TOPIC_PATTERN:
        if topic.lower() in text.lower():return topic
    return None

def explicit_goal(text):
    """Return (goal, heuristic confidence). Negated alternatives win."""
    negated=re.search(r"(開発|作る|作りたい|開発したい)ではなく(学習|勉強)",text)
    if negated:return "learning",1.0
    negated=re.search(r"(学習|勉強)ではなく(開発|作りたい|作る)",text)
    if negated:return "development",1.0
    for name,pattern in INTENT_PATTERNS:
        if re.search(pattern,text):return name,0.95
    if re.search(AMBIGUOUS,text):return None,0.45
    return None,0.0

def question(d):
    if d.topic=="AI" and d.purpose=="development":
        return "どんなAIを作りたいですか？ 会話用LLM、画像認識、その他のAIですか？"
    if d.topic:
        return f"{d.topic}について、学習・開発・エラー解決・雑談のどれに近いですか？"
    return "何について、何をしたいですか？ 雑談でも構いません。"

def ask(d,q,state="DISCOVERING"):
    d.state=state;d.next_action="ASK_CLARIFICATION"
    if q==d.last_question:
        q="今の目的をもう少し具体的に教えてください。学習・開発・エラー解決・雑談でも選べます。"
    d.last_question=q
    return d,"ASK_CLARIFICATION",q

def handoff(d):
    d.state="EXECUTING";d.candidate_purpose=None;d.candidates=[]
    d.missing=[];d.next_action="HANDOFF";d.last_question=None
    if d.purpose=="casual":
        d.next_action="RESPOND"
        return d,"RESPOND","もちろんです。最近気になっていることはありますか？"
    if d.topic is None:
        d.missing=["topic"]
        return ask(d,"何について進めたいですか？")
    return d,"HANDOFF",f"{d.topic}の{LABELS[d.purpose]}を目的として受け付けました。"

def respond(d,text):
    text=text.strip()
    if not text:return ask(d,"どんなことをしたいですか？")
    d.turns+=1
    new_topic=topic_of(text)
    goal,confidence=explicit_goal(text)
    switched=bool(re.search(SWITCH,text))
    if switched and (new_topic or goal):
        d.topic=new_topic or d.topic
        d.purpose=None;d.candidate_purpose=None
        d.last_rejected_purpose=None;d.last_question=None
        d.confidence=0.0
    elif new_topic:
        d.topic=new_topic

    if d.state=="CONFIRMING" and not (goal or switched):
        if re.fullmatch(YES,text,re.I):
            d.purpose=d.candidate_purpose;d.confidence=0.85
            return handoff(d)
        if re.fullmatch(NO,text,re.I):
            d.last_rejected_purpose=d.candidate_purpose
            d.candidate_purpose=None;d.purpose=None;d.confidence=0.0
            d.candidates=[x for x in LABELS if x!=d.last_rejected_purpose]
            d.missing=["user_goal"]
            return ask(d,"では、学習・開発・エラー解決・雑談のどれを希望しますか？")

    if goal:
        d.purpose=goal;d.confidence=confidence
        d.candidate_purpose=None
    elif re.search(AMBIGUOUS,text):
        d.purpose=None;d.confidence=confidence
        d.candidate_purpose="development" if "作" in text else "learning"
        d.candidates=list(LABELS)
        d.missing=["user_goal"]
        q=f"{d.topic or 'そのこと'}を{LABELS[d.candidate_purpose]}したいという理解で合っていますか？"
        d.state="CONFIRMING";d.next_action="ASK_CONFIRMATION";d.last_question=q
        return d,"ASK_CONFIRMATION",q

    if d.purpose=="development" and d.topic=="AI":
        d.candidates=["LLM","画像認識","その他のAI"]
        d.missing=["development_target"]
        return ask(d,question(d))
    if d.purpose:return handoff(d)

    d.purpose=None;d.confidence=0.0
    d.candidates=list(LABELS)
    d.missing=["user_goal"]
    return ask(d,question(d),state="DISCOVERING" if d.topic else "UNKNOWN")

def main():
    d=DSS()
    print("LLM_CHA Purpose Confidence & Confirmation v0.2.31.1")
    print("Commands: /state /reset /quit")
    while True:
        try:line=input("You> ")
        except (EOFError,KeyboardInterrupt):break
        if line.strip()=="/quit":break
        if line.strip()=="/state":
            print(json.dumps(asdict(d),ensure_ascii=False,indent=2));continue
        if line.strip()=="/reset":
            d=DSS();print("DSS reset");continue
        d,action,answer=respond(d,line)
        print(f"CHA[{d.state}/{action},confidence={d.confidence:.2f}]> {answer}")
if __name__=="__main__":main()
