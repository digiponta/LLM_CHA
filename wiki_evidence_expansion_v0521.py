"""v0.5.21 Question-driven expansion of Wikipedia evidence.

Only retrieves a longer extract from the *same resolved article*.
No other article is silently substituted and no new knowledge is trained.
Keyword matching is a conservative heuristic, not semantic entailment.
"""
import re
from wikipedia_acquisition_v0517 import _request
from wiki_answerability_gate_v0522 import evaluate
from wiki_polarity_gate_v0523 import check as polarity_check
from wiki_causal_direction_v0527 import check_direction
from wiki_proposition_alignment_v0524 import align as proposition_align

def intent(question):
    if any(t in question for t in ("なぜ","どうして","理由","原理","仕組み")):return "MECHANISM"
    if any(t in question for t in ("何に使","用途","応用","どこで使")):return "APPLICATION"
    return "OTHER"

CUES={
    "MECHANISM": ("ため","によって","ことで","仕組み","原理","原因","量子干渉"),
    "APPLICATION": ("用途","応用","使用され","利用され","使われ","用いられ","使う","利用する"),
}

def expand(wiki,question,fetch=None):
    kind=intent(question)
    if kind=="OTHER":return {"status":"NOT_APPLICABLE","intent":kind}
    if not isinstance(wiki,dict) or wiki.get("status")!="FOUND":
        return {"status":"NO_CONTEXT","intent":kind}
    title=wiki.get("title","")
    if not isinstance(title,str) or not title or len(title)>100:
        return {"status":"NO_CONTEXT","intent":kind}
    try:
        data=_request({"action":"query","prop":"extracts","titles":title,"redirects":1,
            "explaintext":1,"exchars":4000,"format":"json","formatversion":2},fetch)
        pages=data.get("query",{}).get("pages",[])
        if not pages or pages[0].get("missing") or pages[0].get("title")!=title:
            return {"status":"NO_EVIDENCE","intent":kind}
        excerpt=pages[0].get("extract","")
        if not isinstance(excerpt,str):
            return {"status":"NO_EVIDENCE","intent":kind}
        source=wiki.get("url","")
        if not isinstance(source,str) or not source.startswith("https://ja.wikipedia.org/wiki/"):
            return {"status":"NO_EVIDENCE","intent":kind}
        # A mechanism needs a causal cue; a mere mention of a component
        # cannot explain why a phenomenon occurs.
        sentences=[p.strip() for p in re.split(r"[。\n]",excerpt) if 15<=len(p.strip())<=240]
        candidates=[p for p in sentences if any(c in p for c in CUES[kind])]
        if not candidates:
            return {"status":"NO_EVIDENCE","intent":kind,"source":source}
        answerable=[p for p in candidates if evaluate(p,kind,question)["answerable"]]
        if not answerable:
            return {"status":"NO_ANSWERABLE_EVIDENCE","intent":kind,"source":source,
                    "quality_gate":"ANSWERABILITY_REJECT"}
        aligned=[p for p in answerable if polarity_check(question,p,kind)["supported"]]
        if not aligned:
            return {"status":"NO_SEMANTICALLY_ALIGNED_EVIDENCE","intent":kind,"source":source,
                    "quality_gate":"POLARITY_SUBJECT_REJECT",
                    "reasons":list(dict.fromkeys(polarity_check(question,p,kind)["reason"] for p in answerable))}
        structured=[p for p in aligned if proposition_align(question,p,kind,subject="SQUID" if "SQUID" in title or "超伝導量子干渉計" in title else None)["aligned"]]
        if not structured:
            return {"status":"NO_PROPOSITION_ALIGNMENT","intent":kind,"source":source,
                    "quality_gate":"PROPOSITION_ALIGNMENT_REJECT"}
        directed=[p for p in structured if check_direction(question,p,kind)["supported"]]
        if not directed:
            return {"status":"NO_CAUSALLY_ALIGNED_EVIDENCE","intent":kind,"source":source,
                    "quality_gate":"CAUSAL_DIRECTION_REJECT"}
        selected=directed[0]
        return {"status":"FOUND","intent":kind,"sentence":selected,"source":source,
            "title":title,"truth_state":"EXTERNAL_UNVERIFIED",
            "verified":False,"train_ready":False,"quality_gate":"SOURCE_SPAN_ANSWERABILITY_POLARITY_PROPOSITION_HEURISTIC"}
    except (OSError,ValueError,KeyError,TypeError,TimeoutError) as exc:
        return {"status":"LOOKUP_FAILED","intent":kind,"error":type(exc).__name__}
