"""v0.9.2 — Topic-suggestion intent with corpus-grounded prompts.

A topic suggestion is not a factual knowledge claim. Return topical prompts
with original corpus provenance, never cite the corpus as verified physics.
"""
import re
from pathlib import Path

def topic_request(text):
    q=str(text or "").strip().rstrip("。！？!? 、 ")
    # Restrict to explicit conversational topic requests; never intercept
    # the ordinary definition/QA path.
    if q in ("何か話題はありますか", "何か話題は", "話題は", "話題を教えて",
             "話題を提案して", "何か話そう", "何か話さない"):
        return ""
    match=re.fullmatch(r"(.{2,40}?)(?:的な|に関する|についての|の)(?:話題)(?:は|を教えて|を提案して|ありますか)?",q)
    return match.group(1) if match else None

def suggest(text, corpus_text, fallback_topic=None):
    topic=topic_request(text)
    if topic is None:
        return None
    if not topic:
        topic=fallback_topic or ""
    text=str(corpus_text or "")
    # Keep complete original evidence as a source of suggested discussion,
    # not as endorsed scientific knowledge.
    sentences=[s.strip() for s in re.split(r"(?<=[。！？!?])|\n",text) if s.strip()]
    refs=[]
    if topic:
        refs=[s for s in sentences if topic in s]
    else:
        # Global topic prompts: prefer explicit physics/science mentions,
        # rather than treating the word "話題" as a Wikipedia article.
        refs=[s for s in sentences if any(w in s for w in ("量子力学", "数学", "宇宙"))]
    if not refs:
        return {"route":"TOPIC_SUGGESTION","topic":topic or None,
                "answer":"話題なら、科学や文学について話せる。何に興味がある？",
                "source":"GENERAL_DIALOGUE","evidence_count":0,"verified":False}
    themes=[("粒子と波動","粒子"),("エネルギー準位","エネルギ"),("零点エネルギー","零点"),
            ("宇宙の見方","宇宙"),("数学と物理","数学")]
    selected=[label for label,keyword in themes if any(keyword in s for s in refs)]
    if not selected:
        selected=["原文にある物理学的な考察"]
    options="、".join(selected[:3])
    return {"route":"TOPIC_SUGGESTION_CORPUS",
            "topic":topic or None,
            "answer":f"{topic+'に関係する' if topic else '関連する'}話題なら、{options}がある。どれについて話す？",
            "source":"data/data-nagato.txt","evidence_count":len(refs),
            "evidence_preview":refs[:3],"verified":False}

def suggest_from_file(text,path="data/data-nagato.txt",fallback_topic=None):
    source=Path(path)
    if not source.exists():
        return suggest(text,"",fallback_topic)
    return suggest(text,source.read_text(encoding="utf-8-sig"),fallback_topic)
