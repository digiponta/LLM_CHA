"""Evidence subtopic routing for memory-related corpus statements.

This is lexical classification, not vector semantics or factual verification.
"""
import re
from pathlib import Path

KEYWORDS={
 "VIRTUAL_MEMORY":("仮想メモリ","仮想サーバ","アドレス"),
 "CPU_MEMORY":("メモリのアドレス","命令","CPU"),
 "EXTERNAL_MEMORY":("USBメモリ","外部記憶","外付け"),
 "DATABASE_MEMORY":("オンメモリ","DBMS","三重化"),
 "BIOLOGICAL_MEMORY":("脳の記憶","物忘れ","脳組織"),
}
def classify(text):
    s=str(text or "")
    scores={k:sum(len(w) for w in words if w in s) for k,words in KEYWORDS.items()}
    best=max(scores,key=scores.get)
    return best if scores[best]>0 else "UNCLASSIFIED"

def retrieve(topic,corpus,subtopic=None,max_items=3):
    segments=[p.strip() for p in re.split(r"(?<=[。！？!?])|\n",str(corpus or "")) if p.strip()]
    if topic not in ("メモリ","記憶","記憶装置"):
        return []
    hits=[]
    for idx,s in enumerate(segments):
        if "メモリ" not in s and "記憶" not in s:
            continue
        cls=classify(s)
        if subtopic is not None and cls!=subtopic:
            continue
        hits.append({"text":s,"subtopic":cls,"position":idx,"verified":False})
    return hits[:max_items]

def retrieve_from_file(topic,path="data/data-nagato.txt",subtopic=None):
    source=Path(path)
    if not source.is_file():
        return []
    return retrieve(topic,source.read_text(encoding="utf-8-sig"),subtopic)
