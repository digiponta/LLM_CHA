"""Conservative episodic search and natural Japanese summaries."""
import re

DRINK_ACTIONS={"飲んだ","飲みました"}
EAT_ACTIONS={"食べた","食べました"}
LIKE_ACTIONS={"好み","感想"}
def retrieval_query(text):
 q=(text or "").strip()
 if re.search(r"何を飲んだ|飲んだもの|飲んだ商品",q):return "drank"
 if re.search(r"何を食べた|食べたもの|食べた商品",q):return "ate"
 if re.search(r"どの商品に満足|満足した商品|何に満足",q):return "satisfied"
 if re.search(r"どんな商品が好き|何が好き|好きな商品",q):return "liked"
 return None

def retrieve_episodes(context,query):
 kind=retrieval_query(query)
 if kind is None:return None
 episodes=context.episodes
 if kind=="drank":
  hits=[e for e in episodes if e.action in DRINK_ACTIONS]
 elif kind=="ate":
  hits=[e for e in episodes if e.action in EAT_ACTIONS]
 elif kind=="liked":
  hits=[e for e in episodes if e.action in LIKE_ACTIONS or any(
   "preference" in o.get("dimensions",[]) for o in e.observations)]
 else:
  hits=[e for e in episodes if any(
   any(v.get("attribute")=="満足" and v.get("polarity")=="positive"
       for v in o.get("semantic",[])) for o in e.observations)]
 names=list(dict.fromkeys(e.subject for e in hits))
 if not names:
  return "この会話では、該当する体験や感想は記録されていません。"
 if kind=="drank":
  return "この会話では、"+"、".join(names)+"を飲んだと話していたね。"
 if kind=="ate":
  return "この会話では、"+"、".join(names)+"を食べたと話していたね。"
 if kind=="liked":
  return "この会話では、"+"、".join(names)+"が好きだと話していたね。"
 return "この会話では、"+"、".join(names)+"について満足したと話していたね。"

def natural_summary(episode):
 if not episode or not episode.observations:return None
 clauses=[];seen=set()
 for observation in episode.observations:
  semantics=observation.get("semantic",[])
  for value in semantics:
   attr=value.get("attribute");v=value.get("value");pol=value.get("polarity")
   if attr=="香り" and pol=="positive":clause="香りが良かった"
   elif attr=="苦味" and v=="少し苦い":clause="少し苦かった"
   elif attr=="満足" and pol=="positive":clause="満足した"
   elif attr=="好み" and pol=="positive":clause="好き"
   elif attr=="美味しさ" and pol=="positive":clause="美味しかった"
   else:continue
   if clause not in seen:
    clauses.append(clause);seen.add(clause)
 if not clauses:return None
 return episode.subject+"について、"+"、".join(clauses)+"と話していたね。"
