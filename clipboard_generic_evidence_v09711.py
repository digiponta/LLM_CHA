"""Read-only generic evidence quotes from temporary clipboard context.

Lexical character-bigram TF-IDF. Scores are relevance only, not truth.
"""
from clipboard_evidence_retrieval_v0978 import retrieve

def answer(question, text, min_score=0.16, max_quotes=3):
    q=str(question or "").strip()
    if not q or not text:
        return None
    # Only explicit requests for source evidence; avoid swallowing routine chat.
    prefixes=("このページで","このページには","この文章で","コピーした内容で",
              "引用して","根拠を示して")
    if not (q.startswith(prefixes) or q.endswith(("について記述は？","についての記述は？"))):
        return None
    hits=retrieve(q,text,k=max_quotes,method="tfidf",min_score=min_score)
    if not hits:
        return {"answer":"コピーした範囲には関連する記述を確認できませんでした。",
                "evidence":[],"train_ready":False}
    quotes=" / ".join("「"+h["text"]+"」" for h in hits)
    return {"answer":"コピーした本文にある関連記述（未検証）："+quotes,
            "evidence":hits,"train_ready":False}
