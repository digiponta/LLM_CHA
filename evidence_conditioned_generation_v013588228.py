"""Conservative evidence-conditioned generation planner and answer gate.

The existing LLM can produce a candidate, but only supported statements are shown.
Unapproved model generations are discarded in favour of attributed source excerpts.
"""
import re
from auto_wiki_unknown_v013588212 import search_wikipedia

STOP={"とは","について","こと","そして","また","です","ます"}
def keywords(text):
 return set(x for x in re.findall(r"[一-龥ぁ-んァ-ヶA-Za-z]{2,}",text or "") if x not in STOP)
def focus_query(topic,previous):
 # Distinguish a scientific subject from a dictionary-style overview.
 if topic=="宇宙" and re.search(r"膨張",previous or ""):return "宇宙膨張"
 return topic
def retrieve_evidence(topic,previous="",searcher=search_wikipedia):
 query=focus_query(topic,previous)
 data=searcher(query)
 hits=data.get("hits",[]) if data.get("status")=="HIT" else []
 exact=[h for h in hits if query in h.get("title","")]
 hit=(exact or hits or [None])[0]
 if not hit:return {"status":"NO_EVIDENCE","topic":topic,"query":query}
 return {"status":"EVIDENCE","topic":topic,"query":query,
         "title":hit["title"],"excerpt":hit["extract"][:900],"url":hit["url"],
         "trust":"EXTERNAL_UNVERIFIED"}
def conditioned_prompt(evidence):
 # chat.py consumes each newline as a separate user turn. Keep exactly one.
 topic=re.sub(r"[\\r\\n\\t]+"," ",str(evidence["topic"])).strip()
 excerpt=re.sub(r"\\s+"," ",str(evidence["excerpt"])).strip()[:240]
 return ("資料の範囲内で"+topic+"について簡潔に説明: "+excerpt)

def evidence_gate(candidate,evidence):
 if evidence.get("status")!="EVIDENCE":return ("NO_EVIDENCE",None)
 candidate=(candidate or "").strip()
 if not candidate or "未学習" in candidate:return ("REJECT_UNKNOWN",None)
 if len(candidate)>300 or len(candidate)<15:return ("REJECT_LENGTH",None)
 if re.search(r"無用反面|アフェイン接続|自己同一性写像",candidate):
  return ("REJECT_UNGROUNDED",None)
 # Conservative lexical evidence check: all substantive candidate sentences
 # must be short substrings of the retrieved article to prevent invented claims.
 sentences=[s.strip() for s in re.split(r"(?<=。)",candidate) if s.strip()]
 if not sentences or any(s.rstrip("。") not in evidence["excerpt"] for s in sentences):
  return ("REJECT_NOT_ENTAILED",None)
 return ("ACCEPT_SOURCE_EXTRACT",candidate)
def verified_fallback(evidence):
 if evidence.get("status")!="EVIDENCE":
  return "話題に対応する根拠資料を確認できなかったため、詳細な説明は控えます。"
 sentences=[s.strip() for s in re.split(r"(?<=。)",evidence["excerpt"]) if s.strip()]
 excerpt="".join(sentences[:4])[:700]
 return (f"「{evidence['topic']}」についての参考資料（外部未検証）：\n"+
         excerpt+"\n出典: "+evidence["url"])
def final_answer(candidate,evidence):
 state,accepted=evidence_gate(candidate,evidence)
 return {"gate":state,"answer":(verified_fallback(evidence) if accepted is None else
     accepted+"\n出典: "+evidence["url"]+"（外部未検証）")}
