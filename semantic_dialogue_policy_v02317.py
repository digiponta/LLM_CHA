"""v0.2.31.7 Semantic Dialogue Policy: convert structured purpose into action.

The parser remains frozen. This module is an explicit, inspectable policy;
it does not constitute a learned LLM dialogue policy or task execution.
"""
from dataclasses import dataclass,asdict
import json
from structured_semantic_purpose_v02315 import extract,action_for as old_action

@dataclass
class PolicyDecision:
    action:str
    reason:str
    question:str|None=None
    plan:list[str]|None=None

def decide(s):
    purposes=list(dict.fromkeys(s.purposes))
    if s.status=="NEEDS_CONFIRMATION":
        choice=s.evidence.get("vector_candidate")
        return PolicyDecision("ASK_CONFIRMATION","purpose not explicit",
            question=f"{s.topic or 'そのこと'}について、{choice or 'どのようなこと'}をしたいという理解で合っていますか？")
    if not purposes:
        return PolicyDecision("ASK_CLARIFICATION","missing purpose",
            question=f"{s.topic or '何'}について、どのようなことをしたいですか？")
    if s.status=="NEEDS_CLARIFICATION":
        return PolicyDecision("ASK_CLARIFICATION","insufficient purpose evidence",
            question="目的をもう少し具体的に教えてください。")
    if len(purposes)>1:
        # The parser's ordering is taken as-is; do not invent dependencies.
        return PolicyDecision("PLAN","multiple purposes",
            plan=[f"{i+1}. {purpose}" for i,purpose in enumerate(purposes)])
    if purposes[0]=="casual":
        return PolicyDecision("RESPOND","casual conversation",
            question=f"{s.topic or '最近のこと'}について、どんな話をしましょうか？")
    if s.status=="NEEDS_PLANNING":
        return PolicyDecision("PLAN","planning requested",
            plan=[f"1. {purposes[0]}"])
    return PolicyDecision("HANDOFF","single explicit purpose")

def compare(text):
    s=extract(text)
    old=old_action(s)
    decision=decide(s)
    return {"text":text,"topic":s.topic,"purposes":s.purposes,
            "relation":s.relation,"polarity":s.polarity,"status":s.status,
            "old_action":old,"new_action":decision.action,
            "decision":asdict(decision)}

def main():
    print("LLM_CHA Semantic Dialogue Policy v0.2.31.7")
    print("/quit to exit")
    while True:
        try:line=input("You> ").strip()
        except (EOFError,KeyboardInterrupt):break
        if line=="/quit":break
        print(json.dumps(compare(line),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
