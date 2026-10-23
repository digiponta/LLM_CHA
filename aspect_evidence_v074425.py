"""v0.7.44.25: evidence-only aspect selection after topic follow-ups."""
import re
ASPECTS = {"基本原理":("原理","理論","法則"),"数式":("方程式","数式","式で","演算子"),
           "実験":("実験","観測","測定"),"応用":("応用","利用","技術")}
def choose_aspect(text):
    t=(text or "").strip().rstrip("。！？? ")
    return t if t in ASPECTS else None

def extract_aspect(wiki, aspect):
    if aspect not in ASPECTS or not isinstance(wiki,dict) or wiki.get("status")!="FOUND":
        return None
    extract=wiki.get("extract","")
    source=wiki.get("url","")
    if not isinstance(extract,str) or not isinstance(source,str) or not source.startswith("https://ja.wikipedia.org/wiki/"):
        return None
    from wiki_math_integrity_v074421 import safe_evidence_sentence
    for sentence in re.split(r"[。\n]",extract):
        sentence=sentence.strip()
        if (30<=len(sentence)<=240 and safe_evidence_sentence(sentence)
                and any(k in sentence for k in ASPECTS[aspect])
                and not any(x in sentence for x in ("==", "{", "}", "\\"))):
            return {"answer":"Wikipediaの「"+aspect+"」に関する記述： "+sentence+"。",
                    "source":source,"truth_state":"EXTERNAL_UNVERIFIED",
                    "train_ready":False,"auto_promote":False}
    return None
