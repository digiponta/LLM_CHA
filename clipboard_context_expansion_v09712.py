"""Expand matched headings into neighboring source descriptions, without inference."""
import re
from clipboard_evidence_retrieval_v0978 import retrieve

def expand(question, text, max_items=3):
    lines=[s.strip() for s in str(text or "").splitlines() if s.strip()]
    if not lines:
        return []
    hits=retrieve(question,text,k=8,method="tfidf",min_score=0.12)
    results=[]
    used=set()
    for hit in hits:
        target=hit["text"]
        try:
            pos=lines.index(target)
        except ValueError:
            continue
        # Treat a short title as a heading. Immediately following substantial
        # text is only context, not proof of a semantic relation.
        is_heading=len(target)<85 and not re.search(r"[。.!?]$",target)
        context=[]
        if is_heading:
            for candidate in lines[pos+1:pos+5]:
                if len(candidate)>=75:
                    context.append(candidate)
                    break
        key=(target,tuple(context))
        if key in used:
            continue
        used.add(key)
        results.append({"topic":target,
                        "role":"TOPIC_MATCH" if is_heading else "DESCRIPTION",
                        "description":context[0] if context else None,
                        "description_role":"RELATED_CONTEXT" if context else None,
                        "score":hit["score"],
                        "source_position":pos,
                        "truth_state":"EXTERNAL_UNVERIFIED"})
        if len(results)>=max_items:break
    return results

def answer(question,text):
    hits=expand(question,text)
    if not hits:
        return None
    entries=[]
    for item in hits:
        if item["description"]:
            entries.append(f"「{item['topic']}」— 関連する後続記述：「{item['description']}」")
        else:
            entries.append(f"「{item['topic']}」")
    return "コピーした本文からの関連箇所（未検証）："+ " / ".join(entries)
