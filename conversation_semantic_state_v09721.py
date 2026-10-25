"""Ephemeral typed semantic observations for clipboard-based conversation.

The clipboard source is not verified. User reports are attributed to the user,
not promoted into external factual claims. No disk writes, no embeddings.
"""
from clipboard_product_resolution_v09720 import classify

TASTE_TERMS={"acidity":("酸味","酸っぱ"),"sweetness":("甘さ","甘かった","甘い"),
             "chocolate":("チョコレート",),"bitterness":("苦味","苦い")}
CONCLUSIONS=("満足","満足した","とても満足した","満足だった","よかった",
             "良かった","おいしかった","美味しかった")

class ConversationalSemanticState:
    def __init__(self):
        self.reset()
    def reset(self):
        self.entity=None
        self.event=None
        self.attributes={}
        self.evaluation=None
        self.status="EMPTY"
    def observe(self,utterance,source,dialogue,before):
        q=str(utterance or "").strip().rstrip("。？！? ")
        detected=classify(source,q) if source else None
        # A successful full/alias match begins a new, source-supported topic.
        if detected and detected["status"]=="EXACT" and detected["intent"]=="EXPERIENCE":
            self.entity=detected["product"]
            self.event="consumption"
            self.attributes={}
            self.evaluation=None
            self.status="ACTIVE"
        elif detected and detected["status"]=="EXACT" and detected["intent"]=="TASTE" and not self.entity:
            self.entity=detected["product"]
            self.event="taste_report"
            self.attributes={}
            self.evaluation=None
            self.status="ACTIVE"
        elif detected and detected["status"]=="AMBIGUOUS":
            self.reset()
            return
        # Only collect a follow-up if the dialogue actually consumed it.
        is_followup=(before["taste_turns"]>dialogue.taste_turns and
                     before["taste_turns"]>0 and self.entity is not None)
        is_initial_taste=bool(detected and detected["status"]=="EXACT" and
                              detected["intent"]=="TASTE" and self.entity)
        if is_followup or is_initial_taste:
            for key,terms in TASTE_TERMS.items():
                if any(x in q for x in terms):
                    self.attributes[key]={"reported":True,"provenance":"USER_REPORTED"}
        # Conclusion may be accepted even after the product alias is cleared
        # from ClipboardDialogue; the semantic state is not externally promoted.
        from daily_evaluation_intent_v09729 import classify_evaluation
        explicit=classify_evaluation(utterance)
        in_experience=bool(before["taste_turns"] or before["awaiting_conclusion"])
        if explicit and in_experience and self.entity:
            self.evaluation={"value":q,"emotion":explicit["label"],
                             "provenance":"USER_REPORTED"}
            self.status="CLOSED"
        elif before["awaiting_conclusion"] and q in CONCLUSIONS:
            self.evaluation={"value":q,"provenance":"USER_REPORTED"}
            self.status="CLOSED"
        elif self.status=="ACTIVE" and not (dialogue.taste_turns or dialogue.awaiting_conclusion):
            # Unrelated utterance switches topic; discard transient record.
            self.reset()
    def snapshot(self):
        return {"schema":"conversational-semantic-state-v0.1",
                "entity":self.entity,
                "entity_provenance":"CLIPBOARD_UNVERIFIED" if self.entity else None,
                "event":self.event,"actor":"user" if self.event else None,
                "attributes":dict(self.attributes),"evaluation":self.evaluation,
                "lifecycle":"EPHEMERAL","status":self.status,
                "train_ready":False,"auto_promote":False,"persisted":False}
