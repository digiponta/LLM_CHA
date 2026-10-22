"""v0.6.15 read-only evidence search for concepts occurring outside subject position."""
import re
from pathlib import Path

def normalize_focus(focus):
    focus=str(focus).strip().strip("「」『』 \t。？！!?")
    if not focus or len(focus)>48 or any(c in focus for c in "\r\n/\\"):
        return None
    return focus

def find_mentions(path, focus, max_results=3):
    """Return source-backed statements, not asserted truths or promoted records."""
    term=normalize_focus(focus)
    if not term: return []
    source=Path(path)
    if not source.is_file(): return []
    result=[]
    with source.open(encoding="utf-8-sig") as stream:
        for lineno,line in enumerate(stream,1):
            # Split prose into clauses, and prefer a proposition containing the term.
            for fragment in re.split(r"[。！？!?\n]",line):
                fragment=fragment.strip()
                if term not in fragment or len(fragment)<len(term)+5:
                    continue
                # Reject truncated fragments and overly broad fragments.
                if len(fragment)>320: continue
                result.append({"text":fragment+"。","line":lineno,"term":term,
                               "source":str(source),"truth_state":"UNVERIFIED",
                               "train_ready":False,"auto_promote":False})
                if len(result)>=max_results: return result
    return result

def present_mentions(hits):
    if not hits: return None
    body=" / ".join(hit["text"] for hit in hits)
    return "【原文中の関連記述・未検証】"+body
