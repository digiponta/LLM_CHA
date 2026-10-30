"""Explicit attempt lifecycle; diagnostics count starts, not just completed outputs."""
from dataclasses import dataclass,field
from uuid import uuid4
from collections import Counter

@dataclass
class AttemptTracker:
 attempts:dict=field(default_factory=dict)
 def start(self,topic):
  key=str(uuid4());self.attempts[key]={"id":key,"topic":topic,"state":"STARTED","gate":None}
  return key
 def transition(self,key,state,gate=None):
  if key not in self.attempts:raise KeyError(key)
  item=self.attempts[key]
  if item["state"] in ("COMPLETED","FAILED"):raise ValueError("Terminal attempt")
  item["state"]=state
  if gate is not None:item["gate"]=gate
  return dict(item)
 def report(self):
  counts=Counter(x["state"] for x in self.attempts.values())
  return {"attempts_started":len(self.attempts),
          "completed":counts["COMPLETED"],"failed":counts["FAILED"],
          "in_flight":len(self.attempts)-counts["COMPLETED"]-counts["FAILED"],
          "states":dict(sorted(counts.items()))}
 def reset(self):self.attempts.clear()
