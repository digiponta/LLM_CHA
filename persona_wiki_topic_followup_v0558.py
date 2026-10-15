"""v0.5.58 topic-specific Wikipedia follow-up from existing Wikipedia context.

Only explicit 'Xについて教えて/詳しく' requests are accepted. If a new topic
is identified, fetch its own source rather than reuse unrelated evidence.
No promotion, memory writes or model training.
"""
import re
from unknown_wiki_fallback_v0557 import fallback

TOPIC=re.compile(r"^(?P<term>[^。！？!?]{2,50}?)(?:について|を)(?:詳しく)?(?:教えて|説明して|知りたい)[。！？!? ]*$")

def followup(utterance,current,persona,lookup,render,grounded=None,cache=None):
    if not isinstance(utterance,str) or not isinstance(current,dict) or current.get("status")!="FOUND":
        return {"status":"NO_CONTEXT"}
    m=TOPIC.fullmatch(utterance.strip())
    if not m:return {"status":"NOT_TOPIC_FOLLOWUP"}
    term=m.group("term").strip(" 、")
    if not term or term in ("それ","これ","その話","この話"):
        return {"status":"AMBIGUOUS_TOPIC"}
    source_title=current.get("title","")
    if term==source_title:
        return {"status":"SAME_TOPIC_DEFER"}
    result=fallback(term,utterance,persona,lookup,render,grounded=grounded,cache=cache)
    if result["status"]!="FOUND":return result
    result["route"]="PERSONA_WIKIPEDIA_TOPIC_FOLLOWUP"
    result["previous_topic"]=source_title
    return result
