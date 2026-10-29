"""Topic/attribute resolution and conservative Wikipedia excerpt verification."""
import re
from auto_wiki_unknown_v013588212 import search_term, search_wikipedia

ATTRIBUTES={
 "屈折率":r"屈折率",
 "化学組成":r"化学組成|成分|組成",
 "硬度":r"モース硬度|硬度",
 "産地":r"産地|産出地",
}
ALIASES={"スファレライト":("閃亜鉛鉱","スファレライト","sphalerite"),
         "閃亜鉛鉱":("閃亜鉛鉱","スファレライト","sphalerite")}
def resolve_question(question,active_topic=""):
 q=(question or "").strip().rstrip("？?。．.")
 for attr,words in ATTRIBUTES.items():
  m=re.fullmatch(r"(.+?)の(?:"+words+r")(?:は|って)?",q)
  if m:
   return {"topic":m.group(1).strip(),"attribute":attr}
  if re.fullmatch(r"(?:"+words+r")(?:は|って)?",q) and active_topic:
   return {"topic":active_topic,"attribute":attr}
 return {"topic":search_term(question,active_topic),"attribute":None}

def search_for_question(question,active_topic="",searcher=search_wikipedia):
 resolved=resolve_question(question,active_topic)
 topic=resolved["topic"]
 if not topic:
  return {"status":"NO_HIT","hits":[],"topic":"","attribute":resolved["attribute"]}
 data=searcher(topic)
 if data["status"]!="HIT":
  return {**data,"topic":topic,"attribute":resolved["attribute"]}
 aliases=ALIASES.get(topic,(topic,))
 relevant=[hit for hit in data["hits"] if any(
  a.casefold() in (hit["title"]+" "+hit["extract"]).casefold() for a in aliases)]
 if not relevant:
  return {"status":"NO_HIT","hits":[],"topic":topic,"attribute":resolved["attribute"]}
 if resolved["attribute"] is None:
  exact=next((h for h in relevant if h["title"]==topic),None)
  return {"status":"HIT","hits":[exact or relevant[0]],"topic":topic,"attribute":None}
 attr=resolved["attribute"]
 lines=[]
 for hit in relevant:
  for sentence in re.split(r"(?<=[。！？])|\n",hit["extract"]):
   line=sentence.strip()
   if re.search(ATTRIBUTES[attr],line):
    lines.append({"title":hit["title"],"extract":line,"url":hit["url"]})
 if not lines:
  return {"status":"NO_ATTRIBUTE_EVIDENCE","hits":[],"topic":topic,"attribute":attr}
 return {"status":"HIT","hits":lines[:2],"topic":topic,"attribute":attr}
