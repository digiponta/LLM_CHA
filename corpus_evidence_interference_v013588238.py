"""Corpus/Evidence interference experiment; deliberately diagnostic only.

The corpus passage is shown as a separate source, never treated as Wikipedia.
"""
import json
import re
from pathlib import Path
from difflib import SequenceMatcher

def find_corpus_context(path, terms=("脳","宇宙"), max_chars=360):
    path=Path(path)
    lines=path.read_text(encoding="utf-8-sig").splitlines()
    ranked=[]
    for n,line in enumerate(lines,1):
        line=line.strip()
        if not line:continue
        score=sum(t in line for t in terms)
        if score:
            ranked.append((score,n,line))
    ranked.sort(key=lambda x:(-x[0],x[1]))
    return [{"line":n,"text":line[:max_chars],"matched_terms":[t for t in terms if t in line]} for _,n,line in ranked[:5]]

def variants(topic,evidence,corpus):
    topic=topic.strip()
    evidence=" ".join(evidence.split())[:350]
    corpus=" ".join(corpus.split())[:350]
    return {
      "A_no_context":"人: "+topic+"とは\nAI:",
      "B_wikipedia":"人: 次の外部資料に基づいて"+topic+"を説明: "+evidence+"\nAI:",
      "C_corpus":"人: 次の既存コーパスの文脈を説明: "+corpus+"\nAI:",
      "D_both_separated":"人: "+topic+"について説明。外部資料: "+evidence+" 既存コーパス(別の意味・混同禁止): "+corpus+"\nAI:",
    }

def assess(outputs, wikipedia, corpus):
    report={}
    for key,text in outputs.items():
        text=str(text or "")
        report[key]={
           "candidate":text,
           "wiki_lexical_similarity":round(SequenceMatcher(None,text,wikipedia).ratio(),3),
           "corpus_lexical_similarity":round(SequenceMatcher(None,text,corpus).ratio(),3),
           "mentions_brain":bool(re.search("脳|脳領域",text)),
           "requires_human_semantic_review":True}
    return report
