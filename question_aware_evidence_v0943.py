"""Select corpus text by question intent without changing factual truth state.

Subject relations are preserved for their subject, but incidental mentions
are not presented as definitions of an unrelated object.
"""
from corpus_role_classifier_v0942 import rank_mentions

def question_intent(question):
    q=str(question or "").strip().rstrip("。！？!? ")
    if q.endswith(("とは","って何","とは何","の定義")):
        return "DEFINITION"
    if any(s in q for s in ("考察","について","どう考える","関連する","話題")):
        return "DISCUSSION"
    return "GENERAL"

def select_evidence(topic,corpus,question=None,max_items=2):
    intent=question_intent(question if question is not None else topic+"とは")
    entries=rank_mentions(topic,corpus,max_items=1000)
    if intent=="DEFINITION":
        # A direct definition is optimal; a subject relation is kept visibly
        # separate and never relabelled as a dictionary definition.
        allowed=("DIRECT_DEFINITION","SUBJECT_RELATION","TOPIC_DISCUSSION")
    else:
        allowed=("TOPIC_DISCUSSION","SUBJECT_RELATION","DIRECT_DEFINITION")
    selected=[r for role in allowed for r in entries if r["role"]==role]
    return {"intent":intent,"selected":selected[:max_items],
            "suppressed_incidental":len([r for r in entries if r["role"]=="INCIDENTAL_MENTION"]),
            "has_direct_definition":any(r["role"]=="DIRECT_DEFINITION" for r in selected)}
