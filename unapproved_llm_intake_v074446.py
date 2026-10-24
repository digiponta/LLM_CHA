"""v0.7.44.46: isolated Semantic candidate intake for an unapproved LLM.

No model training, approval, or promotion is performed by this module.
Conflict detection is conservative: only explicit same-subject opposite
polarity predicates are marked as possible contradictions.
"""
import hashlib
import json
import re
from pathlib import Path
from wiki_topic_memory_v074441 import _sentences

DEFAULT_STORE=Path(__file__).resolve().parent/"data"/"unapproved_llm_candidates_v074446.json"

def _read(path):
    p=Path(path)
    if not p.exists(): return {"version":"v0.7.44.46","candidates":[]}
    data=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data,dict) or not isinstance(data.get("candidates"),list):
        raise ValueError("invalid unapproved candidate store")
    return data

def _save(path,data):
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    tmp.replace(p)

def _normalize(sentence):
    return re.sub(r"\s+","",sentence).rstrip("。")

def _parse_claim(sentence):
    """Extremely narrow polarity heuristic; no semantic entailment asserted."""
    m=re.fullmatch(r"(.{2,40}?)は(.{2,90}?)ではない。?",sentence.strip())
    if m:return (m.group(1),m.group(2),False)
    m=re.fullmatch(r"(.{2,40}?)は(.{2,90}?)である。?",sentence.strip())
    if m:return (m.group(1),m.group(2),True)
    return None

def ingest_wikipedia(wiki,path=DEFAULT_STORE):
    if not isinstance(wiki,dict) or wiki.get("status")!="FOUND":
        return {"status":"NO_SOURCE"}
    title=wiki.get("title")
    url=wiki.get("url","")
    if not isinstance(title,str) or not title or not url.startswith("https://ja.wikipedia.org/"):
        return {"status":"INVALID_SOURCE"}
    sentences=list(_sentences(wiki.get("extract","")))
    if not sentences:return {"status":"NO_SAFE_EVIDENCE"}
    data=_read(path)
    added=0; duplicates=0; suspected=0
    for sentence in sentences:
        canonical=_normalize(sentence)
        digest=hashlib.sha256((url+"|"+canonical).encode("utf-8")).hexdigest()[:16]
        if any(row["id"]==digest for row in data["candidates"]):
            duplicates+=1
            continue
        claim=_parse_claim(sentence)
        conflicts=[]
        if claim:
            for row in data["candidates"]:
                other=_parse_claim(row["natural_language"])
                if other and claim[0]==other[0] and claim[1]==other[1] and claim[2]!=other[2]:
                    conflicts.append(row["id"])
        state="REVIEW_CONFLICT" if conflicts else "UNAPPROVED"
        data["candidates"].append({"id":digest,"subject":title,"natural_language":sentence,
            "canonical_text":canonical,"source":url,"source_type":"Wikipedia",
            "truth_state":"EXTERNAL_UNVERIFIED","state":state,
            "suspected_conflicts":conflicts,"train_ready":False,
            "weight_training":False,"approved_memory_export":False})
        added+=1
        suspected+=bool(conflicts)
    _save(path,data)
    return {"status":"STORED","added":added,"duplicates":duplicates,
            "possible_conflicts":suspected,"total":len(data["candidates"]),
            "train_ready":False}

def inspect_candidates(path=DEFAULT_STORE,limit=10):
    data=_read(path)
    return {"status":"OK","count":len(data["candidates"]),
            "candidates":data["candidates"][-limit:],
            "model_weights_updated":False}
