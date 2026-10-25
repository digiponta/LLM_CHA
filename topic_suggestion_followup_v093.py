"""v0.9.3: short-lived topic suggestion follow-up resolution.

Topic suggestions are conversational state, not approved Semantic Memory.
Corpus evidence is unverified and shown as attributed quotations.
"""
import re
from pathlib import Path

THEMES=(("粒子と波動",("粒子","波動","波として")),
        ("エネルギー準位",("エネルギ","順位","準位")),
        ("零点エネルギー",("零点エネルギー",)),
        ("宇宙の見方",("宇宙",)),
        ("数学と物理",("数学",)))
ORDINALS={"最初":0,"一番目":0,"1番目":0,"１番目":0,
          "二番目":1,"2番目":1,"２番目":1,
          "三番目":2,"3番目":2,"３番目":2}

def options_for_suggestion(suggestion):
    if not isinstance(suggestion,dict) or suggestion.get("route")!="TOPIC_SUGGESTION_CORPUS":
        return []
    evidence=suggestion.get("evidence_preview",[])
    # The original topical evidence may be broader than the preview. Extract
    # options explicitly from the answer, which is what the user saw.
    answer=suggestion.get("answer","")
    match=re.search(r"話題なら、(.+?)がある。どれについて話す？",answer)
    if not match:
        return []
    return [item.strip() for item in match.group(1).split("、") if item.strip()]

def resolve_followup(utterance,options):
    q=str(utterance or "").strip().rstrip("。！？!? ")
    if not options:
        return None
    if not any(x in q for x in ("話題","それ","詳しく","教えて")):
        return None
    i=None
    for word,index in ORDINALS.items():
        if word in q:
            i=index
            break
    if i is None and "最後" in q:
        i=len(options)-1
    if i is None and q in ("それについて教えて","それを詳しく","詳しく教えて"):
        i=0 if len(options)==1 else None
    if i is None:
        return None
    if i<0 or i>=len(options):
        return {"status":"OUT_OF_RANGE","option_count":len(options)}
    return {"status":"RESOLVED","index":i,"topic":options[i]}

def explain_followup(utterance,options,corpus_text):
    resolved=resolve_followup(utterance,options)
    if resolved is None:
        return None
    if resolved["status"]=="OUT_OF_RANGE":
        return {"route":"TOPIC_FOLLOWUP_CLARIFICATION",
                "answer":f"候補は{len(options)}件。番号を選んで。","verified":False}
    label=resolved["topic"]
    keywords=dict(THEMES).get(label,(label,))
    # Only show statements that actually exist in the local corpus.
    chunks=[x.strip() for x in re.split(r"(?<=[。！？!?])|\n",str(corpus_text or "")) if x.strip()]
    from response_quality_v094 import best_evidence
    excerpt=best_evidence(chunks,label)
    if excerpt:
        return {"route":"TOPIC_FOLLOWUP_CORPUS","topic":label,
                "answer":f"{label}について。長門コーパスには「{excerpt}」という記述がある。これは原文中の考察であり、検証済みの説明ではない。",
                "source":"data/data-nagato.txt","verified":False}
    return {"route":"TOPIC_FOLLOWUP_NO_EVIDENCE","topic":label,
            "answer":f"{label}について、今のコーパスから根拠となる記述を確認できなかった。",
            "source":"data/data-nagato.txt","verified":False}

def explain_from_file(utterance,options,path="data/data-nagato.txt"):
    source=Path(path)
    text=source.read_text(encoding="utf-8-sig") if source.exists() else ""
    return explain_followup(utterance,options,text)
