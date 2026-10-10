"""Experimental v0.2.33.36 contract for DSS-guided clarification.

Requires explicit injected DSS and memory adapters. Defaults are mocks only;
no actual DSS/Semantic Memory production updates or model training occur.
"""
from dataclasses import dataclass
import argparse,json
from pathlib import Path

@dataclass(frozen=True)
class Assessment:
    kind:str
    subject:str=""
    slot:str=""
    question:str=""
    choices:tuple=()
    value:str=""

class MockDSS:
    def __call__(self,utterance,context):
        if ("昨日の実験" in utterance or "前回の実験" in utterance) and ("続き" in utterance or "再開" in utterance):
            return Assessment("ambiguous","experiment","target","どの実験ですか？ cursor または semantic_memory を指定してください。",("cursor","semantic_memory"))
        return Assessment("known",value=utterance)

class LocalCandidateStore:
    """In-process mock. NOT Semantic Memory."""
    def __init__(self):
        self.records={};self.next_id=0
    def lookup(self,context,subject,slot):
        for r in reversed(list(self.records.values())):
            if r["key"]==(context,subject,slot) and r["state"]=="approved":return r["value"]
        return None
    def propose(self,context,subject,slot,value):
        self.next_id+=1;key=f"candidate-{self.next_id}"
        self.records[key]={"key":(context,subject,slot),"value":value,"state":"pending"}
        return key
    def approve(self,id):
        r=self.records[id]
        if r["state"]!="pending":raise ValueError("Already resolved")
        for other in self.records.values():
            if other["key"]==r["key"] and other["state"]=="approved":other["state"]="superseded"
        r["state"]="approved"
    def reject(self,id):
        if self.records[id]["state"]=="pending":self.records[id]["state"]="rejected"
    def invalidate(self,context,subject,slot):
        for r in self.records.values():
            if r["key"]==(context,subject,slot) and r["state"] in ("approved","pending"):r["state"]="invalidated"

class IntegrationResolver:
    def __init__(self,dss,memory,ttl_turns=4,max_attempts=2):
        if min(ttl_turns,max_attempts)<1:raise ValueError("Invalid limits")
        self.dss=dss;self.memory=memory;self.ttl=ttl_turns;self.maximum=max_attempts
        self.turn=0;self.pending=None
    def clear(self):
        if self.pending and self.pending.get("candidate"):
            self.memory.reject(self.pending["candidate"])
        self.pending=None
    def receive(self,text,context):
        if not context:raise ValueError("Context required")
        self.turn+=1
        if self.pending and (self.pending["context"]!=context or self.turn-self.pending["since"]>self.ttl):
            self.clear()
        if self.pending:
            p=self.pending
            if text.strip() in ("キャンセル","中止"):
                self.clear();return {"status":"cancelled"}
            if p.get("candidate"):return {"status":"confirm_required"}
            value=text.strip().lower()
            if value in p["choices"]:
                id=self.memory.propose(context,p["subject"],p["slot"],value)
                p["candidate"]=id
                return {"status":"confirm","candidate_id":id,"value":value}
            p["attempts"]+=1
            if p["attempts"]>=self.maximum:
                self.clear();return {"status":"abstain"}
            return {"status":"clarify","response":p["question"]}
        a=self.dss(text,context)
        if a.kind=="known":return {"status":"known","value":a.value}
        if a.kind not in ("unknown","ambiguous") or not (a.subject and a.slot and a.question):
            raise ValueError("Invalid DSS assessment")
        saved=self.memory.lookup(context,a.subject,a.slot)
        if saved is not None:return {"status":"resolved","value":saved,"source":"approved_context_memory"}
        self.pending={"context":context,"since":self.turn,"subject":a.subject,"slot":a.slot,
                      "choices":a.choices,"question":a.question,"attempts":0,"candidate":None}
        return {"status":"clarify","response":a.question}
    def confirm(self,accepted,context):
        self.turn+=1;p=self.pending
        if not p or not p.get("candidate"):return {"status":"error"}
        if context!=p["context"] or self.turn-p["since"]>self.ttl:
            self.clear();return {"status":"expired"}
        id=p["candidate"]
        if not accepted:
            self.memory.reject(id);self.pending=None;return {"status":"rejected"}
        self.memory.approve(id)
        value=self.memory.lookup(context,p["subject"],p["slot"])
        self.pending=None
        return {"status":"resolved","value":value}
    def invalidate(self,context,subject,slot):
        self.turn+=1
        if self.pending and self.pending["context"]==context:self.clear()
        self.memory.invalidate(context,subject,slot)
        return {"status":"invalidated"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--demo",action="store_true")
    p.add_argument("--out",default="results/dss_unknown_adapter_v023336.json")
    a=p.parse_args()
    if not a.demo:
        print("Pass --demo: isolated mock only, no live DSS/Memory connected.")
        return
    r=IntegrationResolver(MockDSS(),LocalCandidateStore())
    events=[]
    for kind,value,context in [("receive","昨日の実験の続きをやって","A"),
        ("receive","cursor","A"),("confirm",True,"A"),
        ("receive","前回の実験の続きをやって","A"),
        ("receive","昨日の実験の続きをやって","B")]:
        result=r.confirm(value,context) if kind=="confirm" else r.receive(value,context)
        events.append({"operation":kind,"input":value,"context":context,"result":result})
    out=Path(a.out)
    if out.exists():raise FileExistsError("Refusing overwrite")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"version":"v0.2.33.36","events":events,
       "limitations":["MockDSS and in-process memory only","No production integration",
        "No automatic internal learning"]},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(events,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
