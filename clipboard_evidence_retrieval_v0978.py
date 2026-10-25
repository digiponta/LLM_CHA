"""v0.9.7.8: bounded, source-preserving clipboard evidence ranking.

Uses Japanese character n-gram TF-IDF without external libraries. This is
lexical similarity, NOT LLM_SEM embeddings or verification of truth.
"""
import math
import re
from collections import Counter

def fragments(text):
    lines=[s.strip() for s in str(text or "").splitlines()]
    return list(dict.fromkeys(s for s in lines if len(s)>=5))[:400]

def ngrams(text,n=2):
    value=re.sub(r"\s+","",str(text or "").lower())
    return Counter(value[i:i+n] for i in range(max(0,len(value)-n+1)))

def retrieve(question,text,k=5,method="tfidf",min_score=0.08):
    if method not in ("tfidf","keyword"):
        raise ValueError("Only lexical TF-IDF and keyword baseline supported")
    docs=fragments(text)
    if not question or not docs:
        return []
    terms=[ngrams(d) for d in docs]
    query=ngrams(question)
    if not query:
        return []
    df=Counter()
    for counts in terms:
        df.update(counts.keys())
    size=len(docs)
    idf={term:math.log((size+1)/(count+1))+1 for term,count in df.items()}
    def similarity(counts):
        if method=="keyword":
            return len(set(query)&set(counts))/max(1,len(query))
        keys=set(query)&set(counts)
        dot=sum(query[t]*counts[t]*idf[t]**2 for t in keys)
        qnorm=math.sqrt(sum(v*v*idf.get(t,1)**2 for t,v in query.items()))
        dnorm=math.sqrt(sum(v*v*idf.get(t,1)**2 for t,v in counts.items()))
        return dot/(qnorm*dnorm) if qnorm and dnorm else 0
    hits=[{"text":d,"score":round(similarity(t),5),"position":i,
           "method":method,"truth_state":"EXTERNAL_UNVERIFIED"}
          for i,(d,t) in enumerate(zip(docs,terms))]
    hits=[h for h in hits if h["score"]>=min_score]
    hits.sort(key=lambda h:(-h["score"],h["position"]))
    return hits[:k]

def compare(question,text,k=5):
    return {"query":question,"keyword":retrieve(question,text,k,"keyword"),
            "tfidf":retrieve(question,text,k,"tfidf"),
            "semantic_vector":{"status":"NOT_CONNECTED"},
            "train_ready":False}
