"""Bounded in-memory episodic context for explicit user experiences.

A user statement is recorded as SELF_REPORTED, distinct from external Evidence.
No persistence, semantic promotion, training, or inferred experiences.
"""
import re
from episode_semantic_v013588221 import normalize_observation
from dataclasses import dataclass,field

FEATURES = (
 ("smell",r"香り|匂い|香ばし"),
 ("taste",r"味|美味|おいし|甘|苦|酸っぱ|旨|うま|あっさり"),
 ("vision",r"黄色|赤い|青い|綺麗|きれい|輝|きらきら"),
 ("touch",r"柔らか|やわらか|ふわふわ|もちもち|食感|滑らか"),
 ("hearing",r"音|響き|静か|うるさ"),
 ("emotion",r"嬉し|楽しい|悲し|寂し|怒|イライラ|安心|満足|心地よ"),
 ("preference",r"好き|気に入"),
)
EXPERIENCE = re.compile(r"(.{1,70}?)(?:を)?(飲んだ|飲みました|食べた|食べました|買った|使った)")
QUESTION = re.compile(r"[？?]|(?:とは|の意味|教えて|説明して)")
@dataclass
class Episode:
 topic:str
 subject:str
 action:str
 observations:list=field(default_factory=list)
 evidence_state:str="USER_SELF_REPORTED"

class EpisodeContext:
 def __init__(self,capacity=12):
  self.capacity=capacity
  self.episodes=[]
  self.active=None
 def clear(self):
  self.episodes.clear();self.active=None
 def start(self,topic,subject,action):
  if not topic or not subject:return None
  episode=Episode(topic,subject,action)
  self.episodes.append(episode)
  self.episodes=self.episodes[-self.capacity:]
  self.active=episode
  return episode
 def observe(self,text,topic):
  s=(text or "").strip().rstrip("。")
  if not s or QUESTION.search(s):return []
  match=EXPERIENCE.fullmatch(s)
  if match:
   self.start(topic,match.group(1).strip(),match.group(2))
   return []
  if (not self.active or self.active.topic!=topic) and topic and re.search(r"好き|気に入った|心地よい|満足",s):
   self.start(topic,topic,"感想")
  if not self.active or self.active.topic!=topic:return []
  clauses=[p.strip(" 、。") for p in re.split(r"。|、|けど|けれど|でも|しかし|が、",s) if p.strip()]
  results=[]
  for clause in clauses:
   senses=[name for name,pattern in FEATURES if re.search(pattern,clause)]
   if not senses:continue
   item={"text":clause,"original_utterance":text.strip(),"dimensions":senses,"semantic":normalize_observation(clause),"source":"USER_SELF_REPORTED"}
   if item not in self.active.observations:
    self.active.observations.append(item)
    results.append(item)
  return results
 def summary(self,topic):
  found=[e for e in self.episodes if e.topic==topic]
  if not found:return None
  episode=found[-1]
  if not episode.observations:return None
  return episode.subject+"について、"+ "／".join(x["text"] for x in episode.observations)+"と話していたね。"
