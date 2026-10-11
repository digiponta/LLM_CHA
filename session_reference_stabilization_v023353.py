"""v0.2.33.53: runtime stabilization and session reference safety audit.

This tests the actual runtime adapter with isolated SQLite state, without
loading the GPU model. User should separately verify the interactive chat.py.
"""
import argparse,json,tempfile
from datetime import datetime,timezone,timedelta
from pathlib import Path
from runtime_reference_integration_v023352 import (
    SessionReferenceStore,RuntimeReferenceBridge,handle_reference_input,
    render_reference_reply,
)

class Clock:
    def __init__(self):self.value=datetime(2026,10,11,tzinfo=timezone.utc)
    def __call__(self):return self.value
    def advance(self,seconds):self.value+=timedelta(seconds=seconds)

def evaluate():
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/"references.sqlite3"
        clock=Clock()
        records=[]
        def check(name,passed,**details):
            records.append({"id":name,"passed":bool(passed),**details})
        def create():
            return RuntimeReferenceBridge(SessionReferenceStore(path,clock=clock,ttl_hours=1))
        a=create()
        a.receive("昨日の実験の続きをやって","A")
        r=a.receive("カーソルでお願いします","A")
        approved=a.receive("はい","A")
        check("initial_approval",r["status"]=="confirm" and approved["status"]=="resolved",
              selected=approved.get("value"))
        b=create()
        stored=b.memory.lookup("A","experiment","target")
        resume=b.receive("前回の実験を再開して","A")
        check("restart_approved_reuse",stored=="cursor" and resume["status"]=="resolved",
              stored=stored,status=resume["status"])
        check("restart_isolation",b.memory.lookup("B","experiment","target") is None and
              b.receive("前回の実験を再開して","B")["status"]=="clarify")
        check("normal_chat_fallthrough",handle_reference_input(b,"量子力学とは","A") is None)
        check("no_orphan_confirmation_after_restart",
              handle_reference_input(b,"はい","A") is None)
        b.invalidate("A")
        check("invalidation_persists",create().memory.lookup("A","experiment","target") is None)
        c=create()
        c.receive("昨日の実験の続きをやって","C")
        c.receive("cursor","C")
        reboot=create()
        abandoned=reboot.memory.recover_pending("C")
        check("pending_not_autoapproved_on_restart",
              abandoned==1 and
              reboot.memory.lookup("C","experiment","target") is None and
              handle_reference_input(reboot,"はい","C") is None)
        clock.advance(3600)
        expired=c.receive("はい","C")
        check("expiration_boundary",expired["status"]=="expired" and
              c.memory.lookup("C","experiment","target") is None,status=expired["status"])
        d=create()
        d.receive("昨日の実験の続きをやって","D")
        d.receive("cursor","D")
        switched=d.receive("それよりLLMを勉強したい","D")
        check("switch_does_not_approve",switched["route"]=="real_dss" and
              d.memory.lookup("D","experiment","target") is None)
        e=create()
        e.receive("昨日の実験の続きをやって","E")
        e.receive("cursor","E")
        e.receive("キャンセル","E")
        check("cancel_and_delayed_yes",handle_reference_input(e,"はい","E") is None and
              e.memory.lookup("E","experiment","target") is None)
        f=create()
        f.receive("昨日の実験の続きをやって","F")
        f.receive("cursor","F")
        ambiguous=f.receive("はい、でも違うかも","F")
        check("ambiguous_yes_no_approval",ambiguous["status"]=="confirm_required" and
              f.memory.lookup("F","experiment","target") is None)
        g=create()
        g.receive("昨日の実験の続きをやって","G")
        first=g.receive("cursor","G")["candidate_id"]
        replacement=g.memory.propose("G","experiment","target","semantic_memory")
        rejected=False
        try:g.memory.approve(first)
        except ValueError:rejected=True
        check("stale_pending_id_rejected",rejected and
              g.memory.lookup("G","experiment","target") is None)
        check("status_messages_are_renderable",bool(render_reference_reply({"status":"confirm","value":"cursor"})))
        return {"version":"v0.2.33.53","passed":sum(x["passed"] for x in records),
                "total":len(records),"cases":records,
                "notes":["Actual opt-in runtime bridge and SQLite store; GPU chat smoke test is separate",
                         "SQLite store is a session reference namespace, not factual Semantic Memory",
                         "Reboot intentionally does NOT restore unconfirmed in-memory dialogue state",
                         "No modifications to model weights or /sleep"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/session_reference_stabilization_v023353.json")
    a=p.parse_args();path=Path(a.out)
    if path.exists():raise FileExistsError("Refusing overwrite")
    result=evaluate();path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"passed":result["passed"],"total":result["total"],
                      "failures":[x for x in result["cases"] if not x["passed"]]},
                     ensure_ascii=False,indent=2))
    print("Saved",path)
if __name__=="__main__":main()
