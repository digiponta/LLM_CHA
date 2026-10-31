"""Narrow, provenance-checked paraphrase routing for registered sphalerite facts."""
from pathlib import Path
import re
from sense_retrieval_probe_v013588279 import probe

def classify(question):
    q=re.sub(r"\s+","",str(question)).strip()
    q=q.rstrip("。！？?!")
    if not q:return None
    # Explicit subject and narrowly supported query forms only.
    if q in ("閃亜鉛鉱","閃亜鉛鉱とは","閃亜鉛鉱って何","閃亜鉛鉱について教えて","閃亜鉛鉱を教えて"):
        return ("閃亜鉛鉱とは？","MEMORY_ATOMIC_EXACT")
    if q in ("スファレライト","スファレライトとは","スファレライトって何","スファレライトについて教えて","スファレライトを教えて"):
        return ("スファレライトとは？","MEMORY_EVIDENCE_ALIAS")
    if q in ("閃亜鉛鉱の化学組成は","閃亜鉛鉱の化学式は","スファレライトの化学組成は","スファレライトの化学式は"):
        return ("閃亜鉛鉱の化学組成は？","MEMORY_ATTRIBUTE_NOT_EXPLICIT")
    return None

def route(question,root="."):
    classified=classify(question)
    if classified is None:return None
    canonical,expected=classified
    root=Path(root)
    paths=[root/"data/semantic_propositions_v1090.jsonl",
           root/"data/unified_semantic_memory_v1090.jsonl",
           root/"data/sense_registration_provenance_v013588273.json"]
    if not all(p.is_file() for p in paths):
        return {"answer":"登録知識の保存先を確認できません。","route":"MEMORY_SOURCE_NOT_FOUND"}
    try:
        result=probe(*paths,questions=(canonical,))
        row=result["answers"][0]
        actual="MEMORY_"+row["route"]
        if actual!=expected:return {"answer":"登録済みの根拠を確認できません。","route":"MEMORY_EVIDENCE_NOT_READY"}
        return {"answer":row["answer"],"route":actual}
    except (OSError,ValueError,KeyError,TypeError,UnicodeError):
        return {"answer":"登録知識を確認できません。","route":"MEMORY_READ_ERROR"}
