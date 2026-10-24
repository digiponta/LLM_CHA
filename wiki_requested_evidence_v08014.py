"""v0.8.0.14: extract only explicit, source-backed evidence about requested topic."""
import re
from wiki_fragment_gate_v074428 import coherent_scientific_evidence
from wiki_math_integrity_v074421 import safe_evidence_sentence

def requested_topic_evidence(requested, selected_wiki):
    requested=(requested or "").strip()
    if not requested or not isinstance(selected_wiki,dict):
        return {"status":"NO_EVIDENCE"}
    article=selected_wiki.get("title","")
    extract=selected_wiki.get("extract","")
    # Conservative lexical alias for the specific '古典ビット' example.
    # It is only a mention detector, not a general semantic equivalence claim.
    mentions=(requested,)
    if requested=="古典ビット":
        mentions=("古典ビット","古典的なビット")
    sentences=[x.strip() for x in re.split(r"[。\n]",extract) if x.strip()]
    for sentence in sentences:
        if not any(term in sentence for term in mentions):continue
        if not (coherent_scientific_evidence(sentence) and safe_evidence_sentence(sentence)):continue
        if sentence.endswith(("、","：",":","は","を","が")):continue
        return {"status":"FOUND","answer":"【関連記事からの部分的根拠・未検証】"+sentence+"。",
                "requested_topic":requested,"selected_article":article,
                "source":selected_wiki.get("url",""),"truth_state":"EXTERNAL_UNVERIFIED",
                "train_ready":False}
    return {"status":"NO_EVIDENCE","requested_topic":requested,
            "selected_article":article,"train_ready":False}
