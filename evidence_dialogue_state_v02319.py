"""v0.2.31.9: persistent Evidence-Aware Dialogue State (DSS).

Prototype controller, separate from LLM generation. Purpose estimates are
heuristic and not calibrated. Actions are decisions, not task execution.
"""
from dataclasses import dataclass,field,asdict
import json,re
from evidence_dialogue_policy_v02318 import decide
from structured_semantic_purpose_v02315 import extract
from purpose_confidence_v02311 import topic_of

YES=re.compile(r"^(はい|うん|そうです|その通り|お願いします|yes|y)[。!！\s]*$",re.I)
NO=re.compile(r"^(いいえ|違います|違う|いや|そうじゃない|no|n)[。!！\s]*$",re.I)
SWITCH=re.compile(r"やっぱり|それより|代わりに|変更したい|話題を変え")
JAPANESE={"learning":"学習","development":"開発","troubleshooting":"問題解決","casual":"雑談"}

@dataclass
class DialogueState:
    state:str="UNKNOWN"
    topic:str|None=None
    purposes:list[str]=field(default_factory=list)
    relation:str="UNSPECIFIED"
    pending_purpose:str|None=None
    pending_question:str|None=None
    rejected:list[str]=field(default_factory=list)
    last_question:str|None=None
    question_count:int=0
    turns:int=0
    history:list[dict]=field(default_factory=list)

def action_from_purposes(d):
    if not d.purposes:return "ASK_CLARIFICATION"
    if len(d.purposes)>1:return "PLAN"
    return "RESPOND" if d.purposes[0]=="casual" else "HANDOFF"

def utterance_response(d,action,question=None):
    if action.startswith("ASK"):
        q=question or f"{d.topic or '今の話題'}について、何をしたいですか？ 学習・開発・問題解決・雑談から選べます。"
        if q==d.last_question:
            q="もう少し具体的に、取り組みたいことを教えてください。"
        d.last_question=q;d.question_count+=1
        d.state="CONFIRMING" if action=="ASK_CONFIRMATION" else "DISCOVERING"
        return q
    d.last_question=None
    d.state="EXECUTING" if action in ("HANDOFF","PLAN") else "READY"
    if action=="PLAN":
        return "次の順に進める計画として保持しました："+" → ".join(JAPANESE.get(p,p) for p in d.purposes)
    if action=="RESPOND":
        return f"{d.topic or '最近のこと'}について、どんな話をしましょうか？"
    return f"{d.topic or 'その話題'}の{JAPANESE.get(d.purposes[0],d.purposes[0])}を目的として受け付けました。"

def step(d,text):
    raw=text.strip()
    if not raw:return d,"ASK_CLARIFICATION",utterance_response(d,"ASK_CLARIFICATION")
    d.turns+=1
    new_topic=topic_of(raw)
    switched=bool(SWITCH.search(raw))
    if d.pending_purpose and not switched and YES.fullmatch(raw):
        d.purposes=[d.pending_purpose]
        d.pending_purpose=None;d.pending_question=None
        action=action_from_purposes(d)
        reply=utterance_response(d,action)
    elif d.pending_purpose and not switched and NO.fullmatch(raw):
        if d.pending_purpose not in d.rejected:d.rejected.append(d.pending_purpose)
        d.pending_purpose=None;d.pending_question=None
        d.purposes=[]
        action="ASK_CLARIFICATION"
        reply=utterance_response(d,action,
            f"{d.topic or '今の話題'}について、何をしたいですか？ 学習・開発・問題解決・雑談から選べます。")
    else:
        structure=extract(raw)
        decision=decide(raw,structure)
        if switched:
            d.pending_purpose=None;d.pending_question=None
            d.purposes=[];d.relation="UNSPECIFIED";d.rejected=[]
        if new_topic:d.topic=new_topic
        if decision.action=="ASK_CONFIRMATION":
            candidate=structure.evidence.get("vector_candidate")
            if candidate in d.rejected:candidate=None
            d.pending_purpose=candidate
            d.pending_question=decision.question
            action="ASK_CONFIRMATION" if candidate else "ASK_CLARIFICATION"
            reply=utterance_response(d,action,decision.question if candidate else None)
        elif decision.action=="ASK_CLARIFICATION":
            d.pending_purpose=None;d.pending_question=None
            action="ASK_CLARIFICATION"
            reply=utterance_response(d,action,decision.question)
        else:
            d.purposes=list(decision.purposes)
            d.relation=structure.relation
            d.pending_purpose=None;d.pending_question=None
            d.rejected=[]
            action=decision.action
            reply=utterance_response(d,action)
    d.history.append({"user":raw,"action":action,"response":reply,
                      "topic":d.topic,"purposes":list(d.purposes),"state":d.state})
    return d,action,reply

def main():
    d=DialogueState()
    print("LLM_CHA Evidence-Aware Dialogue State v0.2.31.9")
    print("Commands: /state /reset /quit")
    while True:
        try:raw=input("You> ")
        except (EOFError,KeyboardInterrupt):break
        if raw.strip()=="/quit":break
        if raw.strip()=="/reset":
            d=DialogueState();print("DSS reset");continue
        if raw.strip()=="/state":
            print(json.dumps(asdict(d),ensure_ascii=False,indent=2));continue
        d,action,reply=step(d,raw)
        print(f"CHA[{d.state}/{action}]> {reply}")
if __name__=="__main__":main()
