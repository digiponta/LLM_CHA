"""Cross-session episodic search with provenance and conservative deduplication."""
import re
from approved_episode_retrieval_v013588224 import _valid, _satisfied
from episodic_retrieval_v013588222 import retrieval_query

def kind_for(question):
 q=(question or "").strip()
 if re.fullmatch(r"(?:その時|そのとき|その時は)(?:満足した|満足していた)[？?]?",q):return "followup"
 return retrieval_query(q)

def _matches(record,kind):
 action=record["action"]
 if kind=="drank":return action in ("飲んだ","飲みました")
 if kind=="ate":return action in ("食べた","食べました")
 observations=record.get("observations",[])
 if kind=="liked":
  return action=="好み" or any(
   any(x.get("attribute")=="好み" and x.get("polarity")=="positive" for x in o.get("semantic",[]))
   for o in observations)
 if kind=="satisfied":return _satisfied(record)
 return False

def _signature(r):
 # An approved snapshot and a live session episode may represent the same
 # experience. Compare canonicalized content, never dedup by subject alone.
 import json
 return json.dumps([r.get("topic"),r.get("subject"),r.get("action"),
  [(o.get("original_utterance"),o.get("semantic")) for o in r.get("observations",[])]],
  ensure_ascii=False,sort_keys=True)

class UnifiedEpisodeRetriever:
 def __init__(self,session,gate):
  self.session=session;self.gate=gate
  self.last_reference=None
 def _records(self):
  approved=_valid(self.gate.list_approved())
  live=[]
  for ep in self.session.episodes:
   live.append({"episode_id":None,"topic":ep.topic,"subject":ep.subject,
    "action":ep.action,"observations":ep.observations,
    "provenance":"USER_SELF_REPORTED","approval":"SESSION_UNAPPROVED"})
  seen=set();result=[]
  for r in approved+live:
   signature=_signature(r)
   if signature in seen:continue
   seen.add(signature);result.append(r)
  return result
 def answer(self,question):
  kind=kind_for(question)
  if kind is None:return None
  records=self._records()
  if kind=="followup":
   selected=self.last_reference
   if not selected:return "直前の質問から対象のEpisodeを一つに特定できません。"
   # Re-check current records; revocation must take effect even within a session.
   found=next((r for r in records if _signature(r)==selected),None)
   if not found:
    self.last_reference=None
    return "参照したEpisodeは現在の検索対象にありません。"
   if _satisfied(found):
    return f"{_label(found)}{found['subject']}について、満足したと話していたね。"
   return f"{_label(found)}{found['subject']}に満足したという記録はありません。"
  matched=[r for r in records if _matches(r,kind)]
  self.last_reference=_signature(matched[0]) if len(matched)==1 else None
  if not matched:return "現在の会話と承認済みの記録に、該当するEpisodeはありません。"
  phrases=[]
  suffix={"drank":"を飲んだ","ate":"を食べた","liked":"が好き","satisfied":"に満足した"}[kind]
  for r in matched:
   phrases.append(f"・{r['subject']}{suffix}（{_label(r).strip()}）")
  return "Episode検索結果（ユーザー本人の発言に基づく記録）:\n"+"\n".join(phrases)

def _label(r):
 return "承認済み記録では、" if r.get("approval")=="APPROVED" else "今回の会話では、"
