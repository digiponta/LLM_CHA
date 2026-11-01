"""Read-only RSE knowledge-state compatibility diagnostic, v0.13.58.83.15.

Existing LLM_CHA runtime retrieves TYPED/CANONICAL/UNIFIED knowledge even
when no explicit truth overlay exists. Preserve that distinction in shadow
diagnostics; never equate lack of truth metadata with lack of knowledge.
"""
import argparse,json
from pathlib import Path
from knowledge_state_resolver_v10100 import extract_query_focus
from rse_real_memory_readonly_v013588314 import jsonl
from rse_semantic_theme_v013588312 import select

def inspect(query, unified_path, truth_path):
    rows=jsonl(unified_path)
    truths={str(x.get("concept","")).strip():str(x.get("state","UNVERIFIED")).strip().upper()
            for x in jsonl(truth_path) if x.get("concept")}
    focus=extract_query_focus(query)
    hits=[(i,x) for i,x in enumerate(rows) if focus and str(x.get("concept","")).strip()==focus
          and str(x.get("assistant","")).strip()]
    if not focus:
        state="NON_CONCEPT"
    elif not hits:
        state="MEMORY_NOT_FOUND"
    else:
        state="MEMORY_PRESENT_UNVERIFIED"
    if len(hits)>1:
        state="MEMORY_AMBIGUOUS"
    truth=truths.get(focus,"UNVERIFIED")
    if hits and truth=="TRUE":
        state="MEMORY_VERIFIED_BY_TRUTH"
    if hits and truth in ("FALSE","OUTDATED","CONTESTED"):
        state="MEMORY_TRUTH_RESTRICTED"
    return {"state":state,"focus":focus,"hit_count":len(hits),
            "record_ids":[f"unified:{i}" for i,_ in hits],
            "truth_state":truth,"truth_explicit":focus in truths,
            "legacy_runtime_route":"UNIFIED" if hits else "NO_UNIFIED_HIT",
            "truth_overlay_status":"WARN" if truth=="UNVERIFIED" else truth,
            "answer_preview":str(hits[0][1].get("assistant","")) if hits else None,
            "provenance":str(hits[0][1].get("source","unified-semantic-memory")) if hits else None}

def shadow(query,unified_path,truth_path,candidates):
    m=inspect(query,unified_path,truth_path)
    # Existing runtime may return UNVERIFIED memory with a warning.
    # In shadow mode we expose its answer only as preview; NEVER approve it.
    if m["hit_count"]:
        return {"status":m["state"],"answer":"未学習です" if m["state"]=="MEMORY_TRUTH_RESTRICTED" else None,
                "legacy_answer_preview":m["answer_preview"],"memory":{k:v for k,v in m.items() if k!="answer_preview"},
                "reason":"PRESENT_BUT_NOT_APPROVED_FOR_RSE" if m["state"]=="MEMORY_PRESENT_UNVERIFIED" else "MEMORY_STATUS_RECORDED",
                "live_integration":False,"source":"REAL_MEMORY_SHADOW"}
    candidate=select(query,candidates)
    return {"status":candidate["status"],"answer":candidate["answer"],"memory":m,
            "source":"THEME_RSE" if candidate["status"]=="ANSWER_SELECTED" else "NO_MATCH",
            "live_integration":False,"theme_trace":candidate["trace"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--query",required=True)
    p.add_argument("--unified",default="data/unified_semantic_memory_v1090.jsonl")
    p.add_argument("--truth",default="data/truth_state_v10103.jsonl")
    p.add_argument("--candidates",default="data/rse_theme_examples_v013588312.json")
    a=p.parse_args()
    c=json.loads(Path(a.candidates).read_text(encoding="utf-8-sig"))["candidates"]
    print(json.dumps(shadow(a.query,a.unified,a.truth,c),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
