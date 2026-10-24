"""v0.8.0.13: requested-topic and selected-article context stay distinct."""
from wiki_selection_relation_v08012 import selection_relation

class DualWikiContext:
    def __init__(self):
        self.clear()
    def clear(self):
        self.requested_topic=None
        self.selected_article=None
        self.relation=None
        self.context_status="INACTIVE"
    def select(self,requested,article):
        self.requested_topic=requested
        self.selected_article=article
        self.relation=selection_relation(requested,article)
        self.context_status="ACTIVE"
    def intent(self,utterance):
        if self.context_status!="ACTIVE":return None
        question=(utterance or "").strip().rstrip("。！？!? ")
        if question in ("元の話題について教えて","元の話題に戻って","元の質問について教えて",
                        "古典ビットそのものについて教えて" if self.requested_topic=="古典ビット" else
                        self.requested_topic+"そのものについて教えて"):
            return {"target":"REQUESTED","topic":self.requested_topic}
        if question in ("選んだ記事について詳しく","選択した記事について詳しく","選んだ記事について教えて"):
            return {"target":"SELECTED","topic":self.selected_article}
        if question in ("今の話題は","今の話題を確認"):
            return {"target":"STATUS","topic":self.selected_article}
        return None
    def summary(self):
        return {"requested_topic":self.requested_topic,
                "selected_article":self.selected_article,
                "relation":self.relation,"context_status":self.context_status,
                "truth_state":"EXTERNAL_UNVERIFIED"}
