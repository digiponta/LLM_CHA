"""v0.5.47 persona-first presentation policy for evidence-bounded replies.

Persona controls tone, not factual content, source, or truth-state.
Uses the existing v0.5.19 persona names, no fabricated biography.
"""
from persona_wiki_grounding_v0519 import PERSONA_ENDINGS

def style(persona="nagato"):
    if persona not in PERSONA_ENDINGS:
        persona="neutral"
    if persona=="nagato":
        return {"persona":"nagato","article_intro":"記事を読んだのね。",
                "lookup_intro":"について確認した。",
                "attribution":"Wikipediaには「",
                "attribution_end":"」とある。",
                "article_ending":PERSONA_ENDINGS["nagato"],
                "lookup_ending":"気になる点は？"}
    return {"persona":"neutral","article_intro":"記事を読まれたのですね。",
            "lookup_intro":"について確認しました。",
            "attribution":"Wikipediaには「",
            "attribution_end":"」と記載されています。",
            "article_ending":PERSONA_ENDINGS["neutral"],
            "lookup_ending":"ほかに気になる点はありますか？"}

def apply(utterance,result,explicit=False,persona="nagato"):
    if not isinstance(result,dict) or result.get("status")!="EVIDENCE_FOUND":return result
    fact=result.get("evidence_span")
    topic=result.get("topic")
    if not isinstance(fact,str) or not fact.strip() or not isinstance(topic,str) or not topic.strip():
        return result
    p=style(persona)
    article=(not explicit and isinstance(utterance,str) and
             topic in utterance and any(x in utterance for x in ("記事を読","ニュースを読","記事を見")))
    intro=topic+(p["article_intro"] if article else p["lookup_intro"])
    end=p["article_ending"] if article else p["lookup_ending"]
    answer=intro+p["attribution"]+fact.rstrip("。")+"。"+p["attribution_end"]+end
    return {**result,"answer":answer,"persona":p["persona"],
            "persona_applied":True,"persona_priority":"PRESENTATION_ONLY",
            "response_intent":"ARTICLE_SHARING" if article else "TOPIC_LOOKUP",
            "route":"PERSONA_WIKIPEDIA_REPAIR","evidence_preserved":fact in answer,
            "verified":False,"train_ready":False,"promoted":False}
