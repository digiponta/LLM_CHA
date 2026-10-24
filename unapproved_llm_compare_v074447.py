"""v0.7.44.47: evidence-only unapproved vs approved answer diagnostic.

This module does NOT instantiate, train or represent a second neural LLM.
No unapproved text is promoted into trusted knowledge.
"""
import re
from unapproved_llm_intake_v074446 import _read, DEFAULT_STORE

def _terms(text):
    return set(re.findall(r"[一-龯ぁ-んァ-ヶ]{2,}|[A-Za-z0-9]{2,}",text or ""))

# Avoid free-standing evidence that requires an antecedent.
_CONTEXT_PREFIXES=("それに対して","そのような","これに対して","一方で","上述の","前述の","このような","この場合","それらは","これは","それは")
def requires_context(sentence):
    text=(sentence or "").strip()
    return any(text.startswith(prefix) for prefix in _CONTEXT_PREFIXES)

def unapproved_answer(question,path=DEFAULT_STORE):
    query=(question or "").strip()
    if not query:return {"status":"INVALID_QUESTION"}
    rows=_read(path)["candidates"]
    terms=_terms(query)
    ranked=[]
    for item in rows:
        if item.get("state")!="UNAPPROVED" or item.get("truth_state")!="EXTERNAL_UNVERIFIED":
            continue
        title=item.get("subject","")
        sentence=item.get("natural_language","")
        score=(5 if title and title in query else 0)+len(terms & _terms(title+" "+sentence))
        if score>0 and not requires_context(sentence):ranked.append((score,item))
    if not ranked:return {"status":"NO_STANDALONE_EVIDENCE","train_ready":False}
    ranked.sort(key=lambda pair:(-pair[0],pair[1]["id"]))
    top=ranked[0][1]
    return {"status":"FOUND","answer":"【未承認知識・外部資料・未検証】"+top["natural_language"],
            "candidate_id":top["id"],"source":top["source"],
            "truth_state":"EXTERNAL_UNVERIFIED","train_ready":False,
            "model_generated":False,"quality_gate":"EXACT_STORED_EVIDENCE"}

def compare_answers(question,approved_answer=None,path=DEFAULT_STORE):
    candidate=unapproved_answer(question,path)
    trusted=(approved_answer or "").strip()
    return {"question":question,"unapproved":candidate,
            "approved":{"status":"PROVIDED" if trusted else "NOT_PROVIDED",
                        "answer":trusted or None},
            "comparison_status":"SIDE_BY_SIDE_ONLY",
            "semantically_equivalent":None,"preferred":None,
            "approved_memory_changed":False,"weights_changed":False}
