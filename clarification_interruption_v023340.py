"""LLM_CHA v0.2.33.40 — confirmation interruption and intent switching.

Wraps real DSS purpose controller and shadow reference store; does not modify
production Semantic Memory or model. Explicit goals can interrupt pending
clarification; bare topic words and unknown answers cannot.
"""
import argparse,json,re
from pathlib import Path
from purpose_confidence_v02311 import explicit_goal,topic_of,SWITCH
from real_dss_reference_bridge_v023339 import RealDSSBridge
from semantic_candidate_adapter_v023337 import JsonCandidateStore

class InterruptibleDSSBridge(RealDSSBridge):
    def receive(self,text,context):
        if not context:raise ValueError("context required")
        t=text.strip()
        if not t:return {"status":"empty","response":"入力してください。"}
        resolver=self._resolver(context)
        if resolver.pending:
            # Keep confirmations separate: a user's "yes/no" must never be
            # reinterpreted as a fresh DSS goal or silently approve a candidate.
            if t in ("キャンセル","中止"):
                result=resolver.receive(t,context)
                result["route"]="reference_resolution"
                return result
            goal,confidence=explicit_goal(t)
            # Only an explicit new goal (not an ambiguous desire or a topic
            # label) interrupts. Existing candidate is rejected on clear().
            if goal is not None and confidence>=0.95:
                resolver.clear()
                result=super().receive(t,context)
                result["interruption"]="new_explicit_goal"
                return result
            if re.search(SWITCH,t) and topic_of(t) is not None:
                resolver.clear()
                result=super().receive(t,context)
                result["interruption"]="explicit_topic_switch"
                return result
        return super().receive(t,context)

def demo(path):
    b=InterruptibleDSSBridge(JsonCandidateStore(path))
    events=[]
    for command,text,ctx in [
        ("input","昨日の実験の続きをやって","A"),
        ("input","AIを開発したい","A"),
        ("input","昨日の実験の続きをやって","B"),
        ("input","cursor","B"),
        ("input","それよりLLMを勉強したい","B"),
        ("input","昨日の実験の続きをやって","C"),
        ("input","cursor","C"),
        ("confirm",True,"C"),
        ("input","前回の実験の続きをやって","C"),
    ]:
        result=b.confirm(text,ctx) if command=="confirm" else b.receive(text,ctx)
        events.append({"operation":command,"input":text,"context":ctx,"result":result})
    return events

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--demo",action="store_true")
    p.add_argument("--shadow-store",default="results/interrupt_shadow_v023340.json")
    p.add_argument("--out",default="results/clarification_interruption_v023340.json")
    a=p.parse_args()
    if not a.demo:
        print("Use --demo; shadow candidate store only.")
        return
    path=Path(a.shadow_store);out=Path(a.out)
    if path.exists() or out.exists():raise FileExistsError("Refusing overwrite")
    events=demo(path)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"version":"v0.2.33.40","events":events,
        "real_dss":"purpose_confidence_v02311",
        "reference_assessor":"MockDSS from v0.2.33.36",
        "store":"JSON shadow store; no production memory write"},
        ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps(events,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
