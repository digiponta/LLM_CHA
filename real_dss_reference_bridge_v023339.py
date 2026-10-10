"""v0.2.33.39: actual DSS purpose controller + context-bound clarification.

Uses the real, deterministic purpose_confidence_v02311.DSS/respond API.
Clarification about a prior experiment remains separate from the DSS purpose
teacher memory and from the conditional semantic proposition store.
"""
import argparse,json
from pathlib import Path
from purpose_confidence_v02311 import DSS,respond
from dss_unknown_adapter_v023336 import IntegrationResolver,MockDSS
from semantic_candidate_adapter_v023337 import JsonCandidateStore

class RealDSSBridge:
    def __init__(self,memory,ttl_turns=4):
        self.memory=memory
        self.controllers={}
        self.resolvers={}
        self.ttl_turns=ttl_turns
    def _resolver(self,context):
        if context not in self.resolvers:
            self.resolvers[context]=IntegrationResolver(MockDSS(),self.memory,self.ttl_turns)
        return self.resolvers[context]
    def receive(self,text,context):
        if not context:raise ValueError("context required")
        if not text.strip():return {"status":"empty","response":"入力してください。"}
        # Never send a pending clarification answer through DSS purpose inference.
        r=self._resolver(context)
        if r.pending or self._is_reference(text):
            result=r.receive(text,context)
            result["route"]="reference_resolution"
            return result
        state=self.controllers.setdefault(context,DSS())
        state,action,reply=respond(state,text)
        self.controllers[context]=state
        return {"status":"dss","action":action,"response":reply,
                "state":state.state,"topic":state.topic,"purpose":state.purpose,
                "confidence_kind":state.confidence_kind,"route":"real_dss"}
    @staticmethod
    def _is_reference(text):
        return ("昨日の実験" in text or "前回の実験" in text) and ("続き" in text or "再開" in text)
    def confirm(self,accept,context):
        result=self._resolver(context).confirm(accept,context)
        result["route"]="reference_resolution"
        return result
    def invalidate(self,context):
        return self._resolver(context).invalidate(context,"experiment","target")

def demo(shadow):
    bridge=RealDSSBridge(shadow)
    steps=[("input","LLMを勉強したい","A"),
           ("input","昨日の実験の続きをやって","A"),
           ("input","cursor","A"),
           ("confirm",True,"A"),
           ("input","前回の実験の続きをやって","A"),
           ("input","昨日の実験の続きをやって","B"),
           ("input","AIを開発したい","B")]
    out=[]
    for command,arg,context in steps:
        result=bridge.confirm(arg,context) if command=="confirm" else bridge.receive(arg,context)
        out.append({"operation":command,"input":arg,"context":context,"result":result})
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--demo",action="store_true")
    p.add_argument("--shadow-store",default="results/reference_shadow_v023339.json")
    p.add_argument("--out",default="results/real_dss_reference_bridge_v023339.json")
    a=p.parse_args()
    if not a.demo:
        print("Use --demo. Real deterministic DSS controller; shadow memory only.")
        return
    shadow_path=Path(a.shadow_store);out_path=Path(a.out)
    if shadow_path.exists() or out_path.exists():raise FileExistsError("Refusing to overwrite results")
    events=demo(JsonCandidateStore(shadow_path))
    out_path.parent.mkdir(parents=True,exist_ok=True)
    out_path.write_text(json.dumps({"version":"v0.2.33.39","events":events,
       "actual_dss":"purpose_confidence_v02311.DSS/respond",
       "reference_assessor":"MockDSS (rule-based; NOT DSS ambiguity inference)",
       "candidate_storage":"JSON shadow store, not production Semantic Memory",
       "llm_training":False},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(events,ensure_ascii=False,indent=2))
    print("Saved",out_path)
if __name__=="__main__":main()
