"""Read-only retrieval for explicitly approved, durable episodic records.

Never interprets preferences as consumption; all results remain self-reported.
"""
import re
from episodic_retrieval_v013588222 import retrieval_query

APPROVED="APPROVED"
DRINK={"飲んだ","飲みました"}
EAT={"食べた","食べました"}
def _valid(records):
 return [r for r in records if isinstance(r,dict) and r.get("approval")==APPROVED
         and r.get("provenance")=="USER_SELF_REPORTED" and
         r.get("lifecycle")=="ACTIVE" and r.get("episode_id") and r.get("subject")]

def _satisfied(record):
 return any(isinstance(o,dict) and any(
   isinstance(v,dict) and v.get("attribute")=="満足" and v.get("polarity")=="positive"
   for v in o.get("semantic",[])) for o in record.get("observations",[]))

def approved_query_kind(question):
 q=(question or "").strip()
 if re.search(r"(?:以前|前に|過去|承認済み|記録).*?(?:何を飲んだ|飲んだもの|飲んだ商品)",q):return "drank"
 if re.search(r"(?:以前|前に|過去|承認済み|記録).*?(?:何を食べた|食べたもの|食べた商品)",q):return "ate"
 if re.search(r"(?:以前|前に|過去|承認済み|記録).*?(?:好きな商品|何が好き)",q):return "liked"
 if re.search(r"(?:以前|前に|過去|承認済み|記録).*?(?:どの商品に満足|何に満足)",q):return "satisfied"
 if re.fullmatch(r"(?:その時|そのとき|その時は)(?:満足した|満足していた)(?:[？?])?",q):return "followup_satisfied"
 return None

class ApprovedEpisodeRetriever:
 def __init__(self,gate):
  self.gate=gate
  self.last_referenced_id=None
 def answer(self,question):
  kind=approved_query_kind(question)
  if kind is None:return None
  records=_valid(self.gate.list_approved())
  if kind=="followup_satisfied":
   selected=next((r for r in records if r["episode_id"]==self.last_referenced_id),None)
   if selected is None:return "承認済みEpisodeのどの体験か特定できません。"
   return (f"承認済みの記録では、{selected['subject']}について満足したと話していたね。"
           if _satisfied(selected) else
           f"承認済みの記録では、{selected['subject']}に満足したという記述は確認できません。")
  if kind=="drank":matches=[r for r in records if r.get("action") in DRINK]
  elif kind=="ate":matches=[r for r in records if r.get("action") in EAT]
  elif kind=="liked":matches=[r for r in records if r.get("action") in ("好み","感想") or
                         any("preference" in o.get("dimensions",[]) for o in r.get("observations",[]))]
  else:matches=[r for r in records if _satisfied(r)]
  unique=[];seen=set()
  for r in matches:
   if r["episode_id"] in seen:continue
   seen.add(r["episode_id"]);unique.append(r)
  if not unique:
   self.last_referenced_id=None
   return "承認済みの記録に該当するEpisodeはありません。"
  self.last_referenced_id=unique[-1]["episode_id"] if len(unique)==1 else None
  names="、".join(dict.fromkeys(r["subject"] for r in unique))
  ending={"drank":"を飲んだ","ate":"を食べた","liked":"が好きだ","satisfied":"に満足した"}[kind]
  return "承認済みの記録では、"+names+ending+"と話していたね。"
