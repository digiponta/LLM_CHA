"""Explicit attempt lifecycle; diagnostics count starts, not just completed outputs."""
from dataclasses import dataclass,field
from uuid import uuid4
from collections import Counter

@dataclass
class AttemptTracker:
 attempts:dict=field(default_factory=dict)
 def start(self,topic):
  key=str(uuid4());self.attempts[key]={"id":key,"topic":topic,"state":"STARTED","gate":None,"failure_reason":None,"exception_type":None,"prompt_chars":None,"process_alive":None}
  return key
 def transition(self,key,state,gate=None):
  if key not in self.attempts:raise KeyError(key)
  item=self.attempts[key]
  if item["state"] in ("COMPLETED","FAILED"):raise ValueError("Terminal attempt")
  item["state"]=state
  if gate is not None:item["gate"]=gate
  return dict(item)
 def annotate(self,key,**fields):
  if key not in self.attempts:raise KeyError(key)
  for name in ("failure_reason","exception_type","prompt_chars","process_alive"):
   if name in fields:self.attempts[key][name]=fields[name]
  return dict(self.attempts[key])
 def report(self):
  counts=Counter(x["state"] for x in self.attempts.values())
  reasons=Counter(x["failure_reason"] or x["gate"] or "UNSPECIFIED" for x in self.attempts.values() if x["state"]=="FAILED")
  return {"attempts_started":len(self.attempts),
          "completed":counts["COMPLETED"],"failed":counts["FAILED"],
          "in_flight":len(self.attempts)-counts["COMPLETED"]-counts["FAILED"],
          "states":dict(sorted(counts.items())),
          "failure_reasons":dict(sorted(reasons.items())),
          "recent_attempts":list(self.attempts.values())[-5:]}
 def reset(self):self.attempts.clear()
