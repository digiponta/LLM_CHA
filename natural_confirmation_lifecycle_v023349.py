"""v0.2.33.49 — guarded natural-language confirmation + reference lifecycle.

Experimental adapter on ContextAwareBridge, not installed in chat.py.
Approval is only possible for a live pending candidate, in the same context.
"""
import argparse,json,re,tempfile
from pathlib import Path
from context_aware_clarification_v023345 import ContextAwareBridge
from semantic_candidate_adapter_v023337 import JsonCandidateStore

YES=frozenset(("はい","はい、お願いします","それで合っています","そうです","yes"))
NO=frozenset(("いいえ","いいえ、違います","違います","no"))
def normalized(s):return re.sub(r"[。！!\s]+$","",s.strip()).lower()

class GuardedConfirmationBridge(ContextAwareBridge):
    def receive(self,text,context):
        if not context:raise ValueError("context required")
        pending=self._resolver(context).pending
        answer=normalized(text)
        # Conservative phrase allowlist: compound/qualified assent is not approval.
        if pending and pending.get("candidate") and answer in YES|NO:
            result=self.confirm(answer in YES,context)
            result["confirmation_source"]="explicit_natural_language"
            return result
        if not pending and answer in YES|NO:
            return {"status":"no_confirmation_pending","route":"confirmation_guard",
                    "response":"確認待ちの候補はありません。"}
        return super().receive(text,context)

SCENARIOS=[
 ("yes",["昨日の実験の続きをやって","カーソルの方","はい"],"resolved","cursor"),
 ("no",["昨日の実験の続きをやって","cursor","いいえ"],"rejected",None),
 ("ambiguous_yes",["昨日の実験の続きをやって","cursor","はい、でも違うかも"],"confirm_required",None),
 ("negated_yes",["昨日の実験の続きをやって","cursor","はいではない"],"confirm_required",None),
 ("bare_yes",["はい"],"no_confirmation_pending",None),
 ("interrupted",["昨日の実験の続きをやって","cursor","それよりLLMを勉強したい","はい"],"no_confirmation_pending",None),
 ("cancelled",["昨日の実験の続きをやって","カーソルの方","キャンセル","はい"],"no_confirmation_pending",None),
 ("recover",["昨日の実験の続きをやって","cursor","いいえ","昨日の実験の続きをやって","意味記憶の実験","はい"],"resolved","semantic_memory"),
]
def evaluate():
    rows=[]
    for sid,turns,expected,value in SCENARIOS:
        with tempfile.TemporaryDirectory() as tmp:
            store=JsonCandidateStore(Path(tmp)/"shadow.json")
            bridge=GuardedConfirmationBridge(store)
            trace=[bridge.receive(t,"A") for t in turns]
            saved=store.lookup("A","experiment","target")
            pending=bridge._resolver("A").pending
            result=trace[-1]["status"]
            # For "confirm_required", verify state remains pending and no approval.
            if sid in ("ambiguous_yes","negated_yes"):
                passed=bool(pending and pending.get("candidate")) and saved is None and result=="confirm_required"
            else:
                passed=result==expected and saved==value
            rows.append({"id":sid,"status":result,"expected":expected,"saved":saved,
                         "passed":passed,"pending":bool(pending),
                         "trace":[{"status":r["status"],"route":r.get("route"),"value":r.get("value"),
                                   "source":r.get("confirmation_source")} for r in trace]})
    # Check A approval does not imply B access.
    with tempfile.TemporaryDirectory() as tmp:
        store=JsonCandidateStore(Path(tmp)/"shadow.json")
        bridge=GuardedConfirmationBridge(store)
        for t in ("昨日の実験の続きをやって","cursor","はい"):bridge.receive(t,"A")
        b=bridge.receive("前回の実験を再開して","B")
        isolation=b["status"]=="clarify" and store.lookup("B","experiment","target") is None
    return {"version":"v0.2.33.49","pass_count":sum(r["passed"] for r in rows),
       "total":len(rows),"context_isolation":isolation,"scenarios":rows,
       "limitations":["Guarded adapter, not production chat.py integration",
           "Rule-based natural-language confirmation: finite exact allowlists",
           "Candidate TTL tested separately with injected clock in next audit",
           "Shadow JSON candidate store; no production Semantic Memory updates"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/natural_confirmation_lifecycle_v023349.json")
    a=p.parse_args();path=Path(a.out)
    if path.exists():raise FileExistsError("Refusing overwrite")
    result=evaluate();path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("pass_count","total","context_isolation")},ensure_ascii=False,indent=2))
    print("Saved",path)
if __name__=="__main__":main()
