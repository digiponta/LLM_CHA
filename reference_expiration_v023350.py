"""v0.2.33.50 — stale confirmation and reference expiry safety audit.

A guarded EXPERIMENTAL subclass, not production chat.py integration.
Checks pending candidate ID, expiration, context, and turn limits before approve.
"""
import argparse,json,tempfile
from datetime import datetime,timedelta,timezone
from pathlib import Path
from natural_confirmation_lifecycle_v023349 import GuardedConfirmationBridge,normalized,YES,NO
from semantic_candidate_adapter_v023337 import JsonCandidateStore

class FakeClock:
    def __init__(self):self.value=datetime(2026,10,10,0,0,tzinfo=timezone.utc)
    def __call__(self):return self.value
    def advance(self,seconds):self.value+=timedelta(seconds=seconds)

class ExpiryGuardBridge(GuardedConfirmationBridge):
    def __init__(self,memory,clock,max_confirmation_turns=3):
        super().__init__(memory)
        self.clock=clock
        self.max_confirmation_turns=max_confirmation_turns
        self.confirmation_open={}
        self.turn_count={}
    def _advance(self,context):
        self.turn_count[context]=self.turn_count.get(context,0)+1
    def _live(self,context):
        pending=self._resolver(context).pending
        if not pending or not pending.get("candidate"):return False
        cid=pending["candidate"]
        records=self.memory._read()["records"]
        matches=[r for r in records if r["id"]==cid]
        if len(matches)!=1:return False
        record=matches[0]
        expires=datetime.fromisoformat(record["expires_at"].replace("Z","+00:00"))
        valid=(record["status"]=="pending" and record["context"]==context and
               self.clock()<expires and
               self.turn_count[context]-self.confirmation_open.get(context,-999)<=self.max_confirmation_turns)
        return valid
    def _expire(self,context):
        resolver=self._resolver(context)
        if resolver.pending:resolver.clear()
        self.confirmation_open.pop(context,None)
        return {"status":"expired","route":"confirmation_guard","response":"確認候補の有効期限が切れています。もう一度指定してください。"}
    def confirm(self,accept,context):
        if not context:raise ValueError("context required")
        self._advance(context)
        if not self._live(context):return self._expire(context)
        result=super().confirm(accept,context)
        self.confirmation_open.pop(context,None)
        return result
    def receive(self,text,context):
        if not context:raise ValueError("context required")
        self._advance(context)
        pending=self._resolver(context).pending
        if pending and pending.get("candidate") and not self._live(context):
            return self._expire(context)
        # Do not use GuardedConfirmationBridge.receive for yes/no: its
        # confirm() dispatch would call our override and double-count turns.
        answer=normalized(text)
        if pending and pending.get("candidate") and answer in YES|NO:
            result=self.confirm(answer in YES,context)
            if result["status"] not in ("expired","error"):result["confirmation_source"]="explicit_natural_language"
            return result
        if not pending and answer in YES|NO:
            return {"status":"no_confirmation_pending","route":"confirmation_guard"}
        result=super(GuardedConfirmationBridge,self).receive(text,context)
        updated=self._resolver(context).pending
        if result["status"]=="confirm" and updated and updated.get("candidate"):
            self.confirmation_open[context]=self.turn_count[context]
        elif not updated:self.confirmation_open.pop(context,None)
        return result

def make_bridge(tmp,clock,max_turns=3):
    store=JsonCandidateStore(Path(tmp)/"shadow.json",clock=clock,ttl_hours=1)
    return ExpiryGuardBridge(store,clock,max_turns),store
def setup(bridge,context="A"):
    bridge.receive("昨日の実験の続きをやって",context)
    return bridge.receive("cursor",context)
def evaluate():
    cases=[]
    def record(name,func):
        try:ok,detail=func()
        except Exception as e:ok,detail=False,{"exception":repr(e)}
        cases.append({"id":name,"passed":bool(ok),"detail":detail})
    def within_ttl():
        with tempfile.TemporaryDirectory() as tmp:
            clock=FakeClock();bridge,store=make_bridge(tmp,clock)
            setup(bridge);clock.advance(3599)
            result=bridge.receive("はい","A")
            return result["status"]=="resolved" and store.lookup("A","experiment","target")=="cursor",{"status":result["status"]}
    def after_ttl():
        with tempfile.TemporaryDirectory() as tmp:
            clock=FakeClock();bridge,store=make_bridge(tmp,clock)
            setup(bridge);clock.advance(3601)
            result=bridge.receive("はい","A")
            return result["status"]=="expired" and store.lookup("A","experiment","target") is None,{"status":result["status"]}
    def replay():
        with tempfile.TemporaryDirectory() as tmp:
            clock=FakeClock();bridge,store=make_bridge(tmp,clock)
            setup(bridge);first=bridge.receive("はい","A");second=bridge.receive("はい","A")
            return first["status"]=="resolved" and second["status"]=="no_confirmation_pending",{"first":first["status"],"replay":second["status"]}
    def wrong_context():
        with tempfile.TemporaryDirectory() as tmp:
            clock=FakeClock();bridge,store=make_bridge(tmp,clock)
            setup(bridge,"A");other=bridge.receive("はい","B")
            return other["status"]=="no_confirmation_pending" and store.lookup("A","experiment","target") is None,{"other":other["status"]}
    def stale_after_switch():
        with tempfile.TemporaryDirectory() as tmp:
            clock=FakeClock();bridge,store=make_bridge(tmp,clock)
            setup(bridge);bridge.receive("それよりLLMを勉強したい","A")
            result=bridge.receive("はい","A")
            return result["status"]=="no_confirmation_pending" and store.lookup("A","experiment","target") is None,{"replay":result["status"]}
    def turn_expiry():
        with tempfile.TemporaryDirectory() as tmp:
            clock=FakeClock();bridge,store=make_bridge(tmp,clock,max_turns=2)
            setup(bridge)
            bridge.receive("まだ迷っています","A")
            result=bridge.receive("はい、でも","A")
            final=bridge.receive("はい","A")
            return final["status"]=="expired" and store.lookup("A","experiment","target") is None,{"intermediate":result["status"],"final":final["status"]}
    for name,fn in (("valid_before_ttl",within_ttl),("expired_after_ttl",after_ttl),
                    ("replayed_yes",replay),("cross_context",wrong_context),
                    ("switch_invalidation",stale_after_switch),("turn_limit",turn_expiry)):
        record(name,fn)
    return {"version":"v0.2.33.50","passed":sum(x["passed"] for x in cases),
            "total":len(cases),"cases":cases,
            "limitations":["Experimental guard only; chat.py unchanged",
             "Sequential fake-clock tests, not atomic multi-process race proof",
             "Store timestamps and pending turn counts are separate mechanisms",
             "No production Semantic Memory mutation"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results/reference_expiration_v023350.json")
    a=p.parse_args();path=Path(a.out)
    if path.exists():raise FileExistsError("Refusing overwrite")
    r=evaluate();path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({"passed":r["passed"],"total":r["total"],"cases":r["cases"]},ensure_ascii=False,indent=2))
    print("Saved",path)
if __name__=="__main__":main()
