"""v0.11.2 isolated dialogue bridge; no modification to Nagato runtime.

This module receives a generated answer and a separately supplied semantic-memory
candidate, and creates a clarification ticket. A reviewed user preference is
reused only for exactly the same question+candidate pair, with contextual decisions
requiring context. Never promotes a preference to factual truth.
"""
import json
import hashlib
from pathlib import Path
from semantic_equivalence_router_v0111 import resolve, choose
from semantic_reconciliation_v0110 import ReconciliationStore, canonical_form, render_question, _save

def _key(question, a, b):
    raw=json.dumps([canonical_form(x) for x in (question,a,b)],ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

class DialogueBridge:
    def __init__(self, root="data/semantic_dialogue_v0112"):
        self.root=Path(root)
        self.tickets=ReconciliationStore(self.root/"tickets")
        self.index_dir=self.root/"review_index"

    def compare(self, question, generated_answer, memory_answer, assertion=None, *, context=""):
        key=_key(question, generated_answer, memory_answer)
        index_path=self.index_dir/(key+".json")
        if index_path.is_file():
            prior=json.loads(index_path.read_text(encoding="utf-8"))
            record=self.tickets.get(prior["ticket_id"])
            if record["state"]=="USER_REVIEWED":
                decision=record["review"]["decision"]
                saved_context=record["review"]["context"]
                if decision in ("prefer_a","prefer_b") and (not saved_context or saved_context==context):
                    return {"action":"USER_PREFERENCE","answer":record["preferred_expression"],
                            "ticket_id":record["id"],"approval_state":"NOT_APPROVED",
                            "factual_truth":"UNVERIFIED"}
                if decision=="both_contextual" and saved_context==context:
                    return {"action":"CONTEXT_SPLIT","answer":None,
                            "ticket_id":record["id"],"approval_state":"NOT_APPROVED"}
                if decision=="neither":
                    return {"action":"UNRESOLVED","answer":None,"ticket_id":record["id"]}
        resolved=resolve(question,generated_answer,memory_answer,assertion,store=self.tickets)
        if resolved["action"]=="ASK_USER":
            resolved["message"]=render_question(self.tickets.get(resolved["ticket_id"]))
            resolved["session_key"]=key
        return resolved

    def review(self,ticket_id,decision,*,context=""):
        record=self.tickets.get(ticket_id)
        result=choose(self.tickets,ticket_id,decision,context=context)
        key=_key(record["question"],record["candidates"]["a"]["text"],
                 record["candidates"]["b"]["text"])
        _save(self.index_dir/(key+".json"),{"ticket_id":ticket_id})
        return result

def main():
    import argparse
    p=argparse.ArgumentParser(description="Isolated dialogue reconciliation demonstration")
    p.add_argument("--root",default="data/semantic_dialogue_v0112")
    a=p.parse_args()
    bridge=DialogueBridge(a.root)
    print("Semantic Dialogue Bridge v0.11.2 (/exit to quit)")
    while True:
        q=input("Question> ").strip()
        if q=="/exit":break
        generated=input("Generated A> ").strip()
        memory=input("Memory B> ").strip()
        result=bridge.compare(q,generated,memory)
        print(result.get("message",result))
        if result["action"]=="ASK_USER":
            decision=input("Decision> ").strip()
            if decision not in ("prefer_a","prefer_b","both_contextual","neither"):
                print("No review saved");continue
            ctx=input("Context> ").strip() if decision=="both_contextual" else ""
            print(bridge.review(result["ticket_id"],decision,context=ctx))
if __name__=="__main__":main()
