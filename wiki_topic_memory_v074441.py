"""Wikipedia-derived topic memory. Source evidence stays unverified.

Only approved candidates are eligible for proactive topic suggestions.
Approval here means user permission for suggestion, NOT factual verification
or permission to train model weights.
"""
import hashlib
import json
import re
from pathlib import Path

DEFAULT_STORE=Path(__file__).resolve().parent/"data"/"wiki_topic_memory_v074441.json"

def _load(path):
    p=Path(path)
    if not p.exists():return {"version":"v0.7.44.41","items":[]}
    d=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(d,dict) or not isinstance(d.get("items"),list):
        raise ValueError("Invalid wiki topic memory")
    return d

def _save(path,data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    tmp.replace(p)

def _sentences(extract):
    from wiki_fragment_gate_v074428 import coherent_scientific_evidence
    from wiki_math_integrity_v074421 import safe_evidence_sentence
    for sentence in re.split(r"[。\n]",extract or ""):
        s=sentence.strip()
        if 18<=len(s)<=180 and coherent_scientific_evidence(s) and safe_evidence_sentence(s) and not s.endswith(("、","：",":","は","が","を")):
            yield s+"。"

def learn_candidate(wiki,path=DEFAULT_STORE):
    if not isinstance(wiki,dict) or wiki.get("status")!="FOUND":
        return {"status":"NO_SOURCE"}
    title=wiki.get("title","");url=wiki.get("url","")
    if not title or not url.startswith("https://ja.wikipedia.org/"):
        return {"status":"INVALID_SOURCE"}
    sentences=list(_sentences(wiki.get("extract","")))[:3]
    if not sentences:return {"status":"NO_SAFE_EVIDENCE"}
    key=hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    d=_load(path)
    for item in d["items"]:
        if item["id"]==key:
            return {"status":"EXISTS","id":key,"state":item["state"]}
    d["items"].append({"id":key,"title":title,"url":url,"sentences":sentences,
                       "state":"PENDING","truth_state":"EXTERNAL_UNVERIFIED",
                       "train_ready":False,"weight_training":False})
    _save(path,d)
    return {"status":"CANDIDATE_STORED","id":key,"state":"PENDING"}

def approve_topic(item_id,path=DEFAULT_STORE):
    d=_load(path)
    for item in d["items"]:
        if item["id"]==item_id:
            item["state"]="APPROVED_FOR_TOPIC_ONLY"
            _save(path,d)
            return {"status":"TOPIC_APPROVED","id":item_id}
    return {"status":"NOT_FOUND"}

def suggest_topic(path=DEFAULT_STORE,exclude_title=None):
    d=_load(path)
    for item in d["items"]:
        if item.get("state")=="APPROVED_FOR_TOPIC_ONLY" and item.get("title")!=exclude_title:
            return {"status":"FOUND","id":item["id"],"title":item["title"],"url":item["url"],
                    "answer":"話題の提案。"+item["title"]+"について話してみる？ Wikipediaには「"+item["sentences"][0]+"」とある。（外部資料・未検証）",
                    "truth_state":"EXTERNAL_UNVERIFIED","train_ready":False}
    return {"status":"NO_APPROVED_TOPIC"}

def begin_topic(item_id,path=DEFAULT_STORE):
    """Return evidence-backed opening for an approved topic only."""
    d=_load(path)
    for item in d["items"]:
        if item["id"]==item_id and item.get("state")=="APPROVED_FOR_TOPIC_ONLY":
            sentences=item.get("sentences") or []
            if not sentences:return {"status":"NO_EVIDENCE"}
            detail=sentences[1] if len(sentences)>1 else sentences[0]
            return {"status":"STARTED","title":item["title"],"url":item["url"],
                    "answer":"では、"+item["title"]+"について。Wikipediaには「"+detail+"」とある。どの点が気になる？（外部資料・未検証）",
                    "truth_state":"EXTERNAL_UNVERIFIED","train_ready":False}
    return {"status":"NOT_APPROVED"}

def observe_followup(wiki, path=DEFAULT_STORE, threshold=2):
    """Learn a Wikipedia topic for suggestions after repeated grounded follow-ups.

    This is retrieval-memory learning only; it does not verify truth or
    authorize neural model training.
    """
    if not isinstance(wiki,dict) or wiki.get("status")!="FOUND":
        return {"status":"NO_SOURCE"}
    candidate=learn_candidate(wiki,path)
    if candidate.get("status") not in ("CANDIDATE_STORED","EXISTS"):
        return candidate
    d=_load(path)
    for item in d["items"]:
        if item["id"]==candidate["id"]:
            item["followup_count"]=item.get("followup_count",0)+1
            if item["followup_count"]>=threshold:
                item["state"]="APPROVED_FOR_TOPIC_ONLY"
            _save(path,d)
            return {"status":"TOPIC_LEARNED" if item["state"]=="APPROVED_FOR_TOPIC_ONLY" else "INTEREST_OBSERVED",
                    "id":item["id"],"count":item["followup_count"],
                    "state":item["state"],"truth_state":"EXTERNAL_UNVERIFIED","train_ready":False}
    return {"status":"NOT_FOUND"}
