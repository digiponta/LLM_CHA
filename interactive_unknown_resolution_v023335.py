"""LLM_CHA v0.2.33.35 — Interactive Unknown Resolution (experimental).

This is an isolated, deterministic dialog-state prototype; it does not claim
to call the actual DSS or Semantic Memory runtime. No automatic neural updates.
"""
import argparse,json,re,uuid
from dataclasses import dataclass,asdict,field
from pathlib import Path

@dataclass
class Candidate:
    id:str
    utterance:str
    slot:str
    value:str
    confidence:float
    source:str="user_confirmation"
    status:str="pending"

@dataclass
class Session:
    intent:str=""
    subject:str=""
    pending_slot:str=""
    prompt:str=""
    attempts:int=0
    candidate_id:str=""
    def waiting(self):return bool(self.pending_slot)

class MemoryAdapter:
    """Local experimental candidate registry; not production Semantic Memory."""
    def __init__(self):self.candidates={};self.approved={}
    def propose(self,candidate):self.candidates[candidate.id]=candidate
    def promote(self,id):
        c=self.candidates[id]
        if c.status!="pending":raise ValueError("already resolved")
        c.status="approved";self.approved[(c.utterance,c.slot)]=c.value
    def reject(self,id):self.candidates[id].status="rejected"

class Resolver:
    def __init__(self,store=None,max_attempts=2):
        self.store=store or MemoryAdapter()
        self.state=Session();self.max_attempts=max_attempts
    def parse(self,text):
        t=text.strip()
        if not t:return {"kind":"empty"}
        if re.search(r"(昨日|前回|さっき)の実験",t) and re.search(r"(続き|再開)",t):
            return {"kind":"resume","subject":"previous_experiment","intent":"continue"}
        return {"kind":"known","text":t}
    def receive(self,text):
        t=text.strip()
        if self.state.waiting():
            if t in ("キャンセル","やめる","中止"):
                self.state=Session();return {"status":"cancelled","response":"確認を中止しました。"}
            if not t:return {"status":"clarify","response":self.state.prompt}
            if len(t)>100:return {"status":"clarify","response":"100文字以内で指定してください。"}
            if self.state.pending_slot=="experiment":
                options={"Cursor":"cursor","カーソル":"cursor",
                         "Semantic Memory":"semantic_memory","セマンティックメモリ":"semantic_memory"}
                key=next((v for k,v in options.items() if k.lower() in t.lower()),None)
                if key is None:
                    self.state.attempts+=1
                    if self.state.attempts>=self.max_attempts:
                        self.state=Session()
                        return {"status":"abstain","response":"対象を特定できないため、処理を保留します。"}
                    return {"status":"clarify","response":"Cursor実験かSemantic Memory実験かを教えてください。"}
                cand=Candidate(str(uuid.uuid4()),"previous_experiment","experiment",key,1.0)
                self.store.propose(cand)
                self.state.candidate_id=cand.id
                # Confirm interpretation before promoting persistent knowledge
                return {"status":"confirm","response":f"対象は{key}の実験でよいですか？",
                        "candidate_id":cand.id}
        p=self.parse(t)
        if p["kind"]=="empty":return {"status":"empty","response":"入力してください。"}
        if p["kind"]=="known":return {"status":"unhandled","response":"この試作版では対象の曖昧性確認のみ扱います。"}
        saved=self.store.approved.get(("previous_experiment","experiment"))
        if saved:return {"status":"resolved","response":f"確認済みの{saved}実験を対象として扱います。","value":saved}
        self.state=Session(intent=p["intent"],subject=p["subject"],
            pending_slot="experiment",prompt="どの実験の続きですか？ Cursor、それともSemantic Memory？")
        return {"status":"clarify","response":self.state.prompt}
    def confirm(self,accepted):
        id=self.state.candidate_id
        if not id:return {"status":"error","response":"確認待ちの候補はありません。"}
        if accepted:
            self.store.promote(id)
            value=self.store.candidates[id].value
            self.state=Session()
            return {"status":"resolved","value":value,
                    "response":f"{value}実験を対象として確定しました。"}
        self.store.reject(id);self.state=Session()
        return {"status":"rejected","response":"候補を破棄しました。必要なら対象を指定してください。"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--demo",action="store_true")
    p.add_argument("--out",default="results/interactive_unknown_resolution_v023335.json")
    a=p.parse_args()
    r=Resolver()
    conversation=[]
    if a.demo:
        for s in ("昨日の実験の続きをやって","Cursorの方"):
            conversation.append({"user":s,"result":r.receive(s)})
        conversation.append({"user":"はい","result":r.confirm(True)})
        conversation.append({"user":"昨日の実験の続きをやって",
                             "result":r.receive("昨日の実験の続きをやって")})
        out=Path(a.out)
        if out.exists():raise FileExistsError("Refusing overwrite")
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps({"version":"v0.2.33.35","demo":conversation,
             "candidates":[asdict(c) for c in r.store.candidates.values()],
             "limitations":["In-memory mock registry, not actual DSS/Semantic Memory",
             "Rule-based ambiguity detection, no unknown token recognition",
             "Explicit confirmation required before approval",
             "Approved memory scoped to this demo object, not persisted to production"]},
             ensure_ascii=False,indent=2),encoding="utf8")
        print(json.dumps(conversation,ensure_ascii=False,indent=2))
        print("Saved",out)
    else:
        print("Run with --demo to exercise the isolated resolver.")
if __name__=="__main__":main()
