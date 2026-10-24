"""v0.7.44.27 — deterministic aspect relevance baseline (not embeddings).

Ranks eligible Japanese Wikipedia sentences. Stronger aspect-specific
explanatory terms beat generic keyword mentions. No inferred claims.
"""
import re
from wiki_math_integrity_v074421 import safe_evidence_sentence
from wiki_fragment_gate_v074428 import coherent_scientific_evidence

FEATURES = {
    "基本原理": (("原理", 3), ("基本", 1), ("状態", 1), ("量子", 1), ("記述", 1), ("理論", 1)),
    "数式": (("方程式", 4), ("演算子", 2), ("波動関数", 2), ("式", 1), ("解", 1)),
    "実験": (("実験", 4), ("観測", 3), ("測定", 3), ("検証", 2)),
    "応用": (("応用", 4), ("利用", 3), ("技術", 2), ("装置", 1)),
}
GENERIC = ("根幹を成す理論", "重要であるばかり", "分野である", "ちなむ")

def ranked_evidence(wiki, aspect):
    if aspect not in FEATURES or not isinstance(wiki, dict) or wiki.get("status") != "FOUND":
        return None
    source=wiki.get("url", "")
    extract=wiki.get("extract", "")
    if not isinstance(source,str) or not source.startswith("https://ja.wikipedia.org/wiki/") or not isinstance(extract,str):
        return None
    candidates=[]
    for index, raw in enumerate(re.split(r"[。\n]", extract)):
        sentence=raw.strip()
        if not 30<=len(sentence)<=240 or not coherent_scientific_evidence(sentence):
            continue
        if any(token in sentence for token in ("==","{","}","\\")):
            continue
        features=FEATURES[aspect]
        hits=[(word,weight) for word,weight in features if word in sentence]
        if not hits:
            continue
        score=sum(weight for _,weight in hits)
        score+=2 if any(x in sentence for x in ("ことによって", "により", "に基づき", "表される", "用いられる")) else 0
        score-=3 if any(x in sentence for x in GENERIC) else 0
        # Formula requests require substantive mathematical content, not a name only.
        if aspect=="数式" and not any(x in sentence for x in ("で表", "で記述", "作用", "表す", "解く", "演算")):
            score-=4
        if score<=0:
            continue
        candidates.append((-score,index,sentence))
    if not candidates:
        return None
    negative,index,sentence=min(candidates)
    return {"answer":f"Wikipediaの「{aspect}」に関する記述： {sentence}。",
            "source":source,"truth_state":"EXTERNAL_UNVERIFIED",
            "train_ready":False,"auto_promote":False,
            "score":-negative,"candidate_count":len(candidates),
            "ranking":"ASPECT_LEXICAL_V1"}
