"""v0.4.12 conservative offline definition alignment with polarity/context guards.

Separate from frozen v0.4.10. Extractions are literal spans, not verified facts.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
from article_proposition_alignment_v0410 import align as baseline_align
from external_candidate_store_v0407 import _atomic_write

BLOCK=("ではない","じゃない","ではなく","ではなかった","ではありません","ではございません",
       "ではないので","と仮定","とするなら","かもしれない","らしい","と言われる",
       "とされる","という説","とは限らない","でない")
ENDINGS=("である","です","だ","を指す","を意味する","の一つ","の一種","の一形式")
SENTENCE=re.compile(r"[^。！？\n]+(?:[。！？]|$)")

def _find_subject_marker(sentence, topic):
    if not sentence.startswith(topic):return None
    pos=len(topic)
    if pos<len(sentence) and sentence[pos]=="（":
        depth=0
        while pos<len(sentence) and pos<250:
            c=sentence[pos]
            if c=="（":depth+=1
            elif c=="）":
                depth-=1
                if depth==0:
                    pos+=1
                    break
            pos+=1
        if depth!=0:return None
    if sentence.startswith("とは",pos):pos+=2
    elif sentence.startswith("は",pos):pos+=1
    else:return None
    while pos<len(sentence) and sentence[pos] in "、 \t":pos+=1
    return pos

def _predicate(sentence, topic):
    start=_find_subject_marker(sentence,topic)
    if start is not None:
        p=sentence[start:].rstrip("。！？").strip()
        if _allow(p):return p,"FORWARD_DEFINITION"
    # Reverse-copula classification, topic exact and sentence-end only.
    marker="が"+topic+"である"
    if sentence.endswith(marker+"。") or sentence.endswith(marker):
        p=sentence[:-(len(marker)+int(sentence.endswith("。")))]
        if p and len(p)<=200 and _allow(p+"である"):
            return p+"である","REVERSE_DEFINITION"
    return None,None

def _allow(p):
    return (2<=len(p)<=200 and p.endswith(ENDINGS)
            and not any(b in p for b in BLOCK)
            and not any(c in p for c in "「」『』？?！!")
            and not p.startswith(("もし","仮に","例えば","仮定して")))

def align(evidence):
    # Reuse all v0.4.10 input validation and hash integrity checks.
    base=baseline_align(evidence)
    source=evidence["lead_extract"];topic=evidence["concept"].strip()
    props=[]
    for m in SENTENCE.finditer(source):
        sentence=m.group().strip()
        if not sentence or any(c in sentence for c in "「」『』"):continue
        if sentence.endswith(("？","！")):continue
        predicate,pattern=_predicate(sentence,topic)
        if predicate is None:continue
        start=m.start()+len(m.group())-len(m.group().lstrip())
        end=start+len(sentence)
        if source[start:end]!=sentence:raise ValueError("source span mismatch")
        props.append({"subject":topic,"predicate":predicate,
                      "proposition_literal":sentence,"evidence_start":start,
                      "evidence_end":end,"evidence_text":sentence,
                      "alignment":"EXACT_LITERAL_SPAN","pattern":pattern,
                      "factual_truth":"UNVERIFIED","review_state":"PENDING_REVIEW",
                      "eligible_for_training":False})
    base.update({"version":"v0.4.12","alignment_type":"GUARDED_RULE_BASED_EXTRACTIVE",
                 "proposition_count":len(props),"propositions":props})
    return base

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--evidence",required=True)
    parser.add_argument("--report")
    a=parser.parse_args()
    try:
        path=Path(a.evidence)
        if path.stat().st_size>128_000:raise ValueError("evidence too large")
        d=align(json.loads(path.read_text(encoding="utf-8")))
        if a.report:
            if Path(a.report).resolve()==path.resolve():raise ValueError("refusing overwrite")
            _atomic_write(a.report,d)
        print(json.dumps(d,ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as e:
        parser.exit(1,f"v0.4.12 failed: {type(e).__name__}: {e}\n")
if __name__=="__main__":main()
