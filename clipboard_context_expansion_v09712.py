"""v0.9.7.13 — source-ordered heading association with response deduplication.

Heuristic for manually copied plaintext: a short heading owns the following
long description only if it appears directly after the heading. An exact
topic heading takes precedence over loosely matching surrounding headings.
"""
import re
from clipboard_evidence_retrieval_v0978 import retrieve

def _lines(text):
    return [line.strip() for line in str(text or "").splitlines() if line.strip()]

def _heading(line):
    return len(line)<85 and not re.search(r"[。.!?]$",line)

def _requested_heading(question, lines):
    q=str(question or "").lower()
    candidates=[line for line in lines if _heading(line) and len(line)>=5 and line.lower() in q]
    return max(candidates,key=len) if candidates else None

def expand(question,text,max_items=3):
    lines=_lines(text)
    if not lines:
        return []
    selected=_requested_heading(question,lines)
    hits=retrieve(question,text,k=8,method="tfidf",min_score=0.12)
    if selected:
        hits=[{"text":selected,"score":1.0}]+[
            hit for hit in hits if hit["text"]!=selected]
    results=[]
    used_text=set()
    for hit in hits:
        target=hit["text"]
        if target in used_text:
            continue
        try:
            pos=lines.index(target)
        except ValueError:
            continue
        # In exact topic queries only the exact heading and its immediately
        # adjacent description are promoted to the answer. Prevents assigning
        # a paragraph to a neighboring, unrelated heading.
        if selected and target!=selected:
            continue
        is_heading=_heading(target)
        description=None
        if is_heading and pos+1<len(lines):
            following=lines[pos+1]
            if len(following)>=75 and not following.startswith(("http://","https://")):
                description=following
        used_text.add(target)
        if description:
            used_text.add(description)
        results.append({
            "topic":target,
            "role":"TOPIC_MATCH" if is_heading else "DESCRIPTION",
            "description":description,
            "description_role":"RELATED_CONTEXT" if description else None,
            "score":hit["score"],"source_position":pos,
            "truth_state":"EXTERNAL_UNVERIFIED"})
        if len(results)>=max_items:
            break
    return results

def answer(question,text):
    hits=expand(question,text)
    if not hits:
        return None
    entries=[]
    seen=set()
    for item in hits:
        title=item["topic"]
        desc=item["description"]
        if title not in seen:
            seen.add(title)
            entries.append(f"「{title}」")
        if desc and desc not in seen:
            seen.add(desc)
            entries.append(f"関連する後続記述：「{desc}」")
    return "コピーした本文からの関連箇所（未検証）："+ " / ".join(entries)
