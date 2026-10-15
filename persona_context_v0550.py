"""v0.5.50: short-lived, non-learning persona conversation context.

Tracks only an explicit article-sharing topic. Follow-up is a user report,
not an externally verified knowledge proposition. One continuation only.
"""
import re
from persona_conversation_router_v0549 import classify,respond
from unified_persona_controller_v0548 import persona_for

FOLLOWUP=re.compile(r"^(?P<detail>[^。！？!?]{2,70}?)(?:について)?(?:書かれていた|載っていた|紹介されていた|と書いてあった)[。！! ]*$")

class PersonaContext:
    def __init__(self,persona="nagato"):
        self.persona=persona_for(persona)
        self.topic=None
    def clear(self):
        self.topic=None
    def handle(self,user):
        intent=classify(user)
        if intent["intent"]=="ARTICLE_SHARING":
            self.topic=intent["topic"]
            return respond(user,self.persona)
        if intent["intent"]=="DAILY_SHARING":
            self.clear()
            return respond(user,self.persona)
        if not isinstance(user,str) or not user.strip() or user.startswith("/"):
            return None
        # Explicit questions must take the established knowledge route.
        if any(x in user for x in ("？","?","教えて","とは","なぜ","どう","何","説明して")):
            self.clear()
            return None
        m=FOLLOWUP.fullmatch(user.strip())
        if self.topic is not None and m:
            detail=m.group("detail").strip()
            if not detail:
                self.clear();return None
            topic=self.topic
            self.clear()
            text=(f"そう。{topic}の記事には{detail}について書かれていたのね。何が印象に残った？"
                 if self.persona=="nagato" else
                 f"{topic}の記事には{detail}について書かれていたのですね。何が印象に残りましたか？")
            return {"answer":text,"route":"PERSONA_CONTEXT_CONTINUATION",
                "persona":self.persona,"intent":"ARTICLE_DETAIL_SHARING",
                "context_topic":topic,"user_reported_detail":detail,
                "truth_state":"USER_REPORTED_UNVERIFIED",
                "knowledge_asserted":False,"verified":False,
                "train_ready":False,"auto_lookup":False,"auto_promote":False}
        self.clear()
        return None
