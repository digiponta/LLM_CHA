"""v0.4.7 isolated external candidate store (never Semantic Memory).

Ingest validated v0.4.6 Wikipedia search results, deduplicate by
concept + article URL, track source excerpt changes, preserve human review.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit

SCHEMA="llm-cha-external-candidates-v0.4.7"
MAX_INPUT_BYTES=512_000
MAX_STORE_BYTES=2_000_000
REVIEW_STATES={"PENDING_REVIEW","NEEDS_REREVIEW","APPROVED_FOR_REVIEW_ONLY","REJECTED"}

def _read_json(path, limit):
    p=Path(path)
    if p.stat().st_size>limit:raise ValueError("file exceeds size limit")
    return json.loads(p.read_text(encoding="utf-8"))

def _candidate(raw, concept):
    if not isinstance(raw,dict):raise ValueError("invalid candidate")
    for key in ("concept","title","url","retrieved_at_utc"):
        if not isinstance(raw.get(key),str) or not raw[key].strip():
            raise ValueError("candidate missing "+key)
    if raw["concept"]!=concept or raw.get("source")!="WIKIPEDIA_SEARCH_RESULT":
        raise ValueError("invalid candidate source or concept")
    if raw.get("factual_truth")!="UNVERIFIED" or raw.get("review_state")!="PENDING_REVIEW":
        raise ValueError("candidate must remain unverified")
    if raw.get("eligible_for_training") is not False or raw.get("is_full_article") is not False:
        raise ValueError("candidate safety flags invalid")
    url=raw["url"]
    parsed=urlsplit(url)
    if parsed.scheme!="https" or parsed.netloc!="ja.wikipedia.org" or not parsed.path.startswith("/wiki/") or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("unexpected Wikipedia URL")
    title=raw["title"].strip()
    desc=raw.get("description","")
    excerpt=raw.get("search_excerpt","")
    if not isinstance(desc,str) or not isinstance(excerpt,str) or len(desc)>500 or len(excerpt)>500 or len(title)>200:
        raise ValueError("invalid excerpt length")
    fingerprint=hashlib.sha256(json.dumps([title,desc,excerpt],ensure_ascii=False,separators=(",",":")).encode("utf-8")).hexdigest()
    key=hashlib.sha256(json.dumps([concept,url],ensure_ascii=False,separators=(",",":")).encode("utf-8")).hexdigest()[:24]
    return {"id":key,"concept":concept,"title":title,"url":url,
            "description":desc,"search_excerpt":excerpt,"source":"WIKIPEDIA_SEARCH_RESULT",
            "retrieved_at_utc":raw["retrieved_at_utc"],"content_sha256":fingerprint,
            "factual_truth":"UNVERIFIED","review_state":"PENDING_REVIEW",
            "eligible_for_training":False,"is_full_article":False,"history":[]}

def _store(path):
    p=Path(path)
    if not p.exists():return {"schema":SCHEMA,"records":[]}
    obj=_read_json(p,MAX_STORE_BYTES)
    if not isinstance(obj,dict) or obj.get("schema")!=SCHEMA or not isinstance(obj.get("records"),list):
        raise ValueError("invalid store schema; refusing overwrite")
    ids=set()
    for row in obj["records"]:
        if not isinstance(row,dict) or not isinstance(row.get("id"),str) or row["id"] in ids or row.get("review_state") not in REVIEW_STATES:
            raise ValueError("invalid stored record")
        if row.get("factual_truth")!="UNVERIFIED" or row.get("eligible_for_training") is not False:
            raise ValueError("store contains invalid training/truth flags")
        ids.add(row["id"])
    return obj

def _atomic_write(path,obj):
    target=Path(path)
    encoded=json.dumps(obj,ensure_ascii=False,indent=2).encode("utf-8")
    if len(encoded)>MAX_STORE_BYTES:raise ValueError("store exceeds size limit")
    target.parent.mkdir(parents=True,exist_ok=True)
    tmp=None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent,prefix=".extcand-",suffix=".tmp",delete=False) as fp:
            tmp=Path(fp.name)
            fp.write(encoded)
            fp.flush()
            os.fsync(fp.fileno())
        os.replace(tmp,target)
    finally:
        if tmp is not None and tmp.exists():tmp.unlink()

def ingest(report_path,store_path):
    report=_read_json(report_path,MAX_INPUT_BYTES)
    if (not isinstance(report,dict) or report.get("version")!="v0.4.6"
        or report.get("source")!="Wikipedia (ja)"
        or report.get("truth_promotions")!=0 or report.get("semantic_memory_writes")!=0
        or report.get("training_enabled") is not False
        or not isinstance(report.get("concept"),str)
        or not isinstance(report.get("candidates"),list)
        or len(report["candidates"])>5
        or report.get("candidate_count")!=len(report["candidates"])):
        raise ValueError("not a valid v0.4.6 research report")
    rows=[_candidate(x,report["concept"]) for x in report["candidates"]]
    if len({r["id"] for r in rows})!=len(rows):raise ValueError("duplicate candidate in report")
    if Path(report_path).resolve()==Path(store_path).resolve():raise ValueError("source and destination must differ")
    store=_store(store_path)
    existing={r["id"]:r for r in store["records"]}
    stats={"added":0,"unchanged":0,"updated":0}
    for row in rows:
        old=existing.get(row["id"])
        if old is None:
            store["records"].append(row)
            existing[row["id"]]=row
            stats["added"]+=1
        elif old.get("content_sha256")==row["content_sha256"]:
            stats["unchanged"]+=1
        else:
            history=old.get("history",[])
            if not isinstance(history,list) or len(history)>=20:raise ValueError("candidate update history limit")
            history.append({"content_sha256":old["content_sha256"],
                            "description":old.get("description",""),
                            "search_excerpt":old.get("search_excerpt",""),
                            "retrieved_at_utc":old.get("retrieved_at_utc",""),
                            "previous_review_state":old["review_state"]})
            old.update({k:row[k] for k in ("title","description","search_excerpt","retrieved_at_utc","content_sha256")})
            old["history"]=history
            old["review_state"]="NEEDS_REREVIEW"
            old["factual_truth"]="UNVERIFIED"
            old["eligible_for_training"]=False
            stats["updated"]+=1
    _atomic_write(store_path,store)
    return {"version":"v0.4.7","store":str(store_path),"record_count":len(store["records"]),
            **stats,"semantic_memory_writes":0,"truth_promotions":0,"training_enabled":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,help="Existing v0.4.6 report JSON")
    p.add_argument("--store",default="results/external_candidate_store_v0407.json")
    a=p.parse_args()
    try: result=ingest(a.input,a.store)
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
        p.exit(1,f"Candidate ingestion failed: {type(exc).__name__}: {exc}\n")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
