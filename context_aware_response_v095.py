"""v0.9.5: context-bound, provenance-safe reflective responses.

No free-form opinions are invented, and corpus propositions remain unverified.
"""
import re
from pathlib import Path

def explicit_opinion_topic(message):
    import re
    q=str(message or "").strip().rstrip("。！？!? ")
    m=re.fullmatch(r"(.{1,40}?)について(?:貴方|あなた)はどう思う",q)
    return m.group(1).strip() if m else None

def opinion_request(message):
    return str(message or "").strip().rstrip("。！？!? ") in (
        "貴方はどう思う","あなたはどう思う","どう思う","それについてどう思う",
        "それをどう思う","意見は","あなたの意見は","貴方の意見は")

class ContextualResponse:
    def __init__(self):
        self.topic=None
        self.source=None
        self.evidence=[]
    def set_topic(self,topic,source,evidence=()):
        if topic:
            self.topic=str(topic)
            self.source=str(source)
            self.evidence=list(evidence or [])
    def reset(self):
        self.topic=self.source=None
        self.evidence=[]
    def respond(self,question):
        explicit=explicit_opinion_topic(question)
        if not opinion_request(question) and explicit is None:
            return None
        if explicit and explicit != self.topic:
            self.set_topic(explicit,"USER_REQUEST")
        if not self.topic:
            return {"route":"CONTEXT_OPINION_CLARIFICATION",
                    "answer":"どの話題についての意見を求めている？",
                    "train_ready":False}
        if self.evidence and self.source=="NAGATO_CORPUS":
            answer=(f"{self.topic}について。長門コーパスには「{self.evidence[0]}」という記述がある。"
                    "これは原文の考察で、事実として検証されていない。どの点を検討したい？")
        else:
            answer=(f"{self.topic}について、今の情報だけでは根拠に基づく独自の評価はできない。"
                    "具体的な論点があれば一緒に検討できる。")
        return {"route":"CONTEXT_AWARE_OPINION","answer":answer,
                "topic":self.topic,"source":self.source,
                "train_ready":False,"verified":False}
