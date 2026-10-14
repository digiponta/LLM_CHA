#!/usr/bin/env python3
"""LLM_CHA v0.4.28.72: size/traceability comparison only.

Full, Minimal and Semantic-only representations are experimental projections,
NOT approved replacements for the v0.4.28.70 evidence gate. Never delete the
conversation from this module. No model learning or source-corpus redistribution.
"""
import argparse
import hashlib
import json
from pathlib import Path
from benchmark_long_conversation_resources_v042871 import make_session
from conversation_sleep_backend_v042868 import extract

VERSION="v0.4.28.72.1"

def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def serialized_size(data):
    return len((json.dumps(data,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))

def project(memory,mode):
    if mode not in ("full","minimal","semantic_only"):raise ValueError("invalid mode")
    candidates=extract(memory)["candidates"]
    turns={t["turn_id"]:t for t in memory["turns"]}
    unique={}
    for p in candidates:
        key=(p["speaker"],p["predicate"],p["object"],p["polarity"])
        entry=unique.setdefault(key,{"speaker":p["speaker"],"predicate":p["predicate"],
           "object":p["object"],"polarity":p["polarity"],"turn_ids":[]})
        entry["turn_ids"].append(p["source_turn"])
    records=[]
    for p in candidates:
        t=turns[p["source_turn"]]
        base={"turn_id":p["source_turn"],"speaker":p["speaker"],
             "relation":p["predicate"],"object":p["object"],"polarity":p["polarity"]}
        if mode=="full":
            base["original_utterance"]=t["text"]
        elif mode=="minimal":
            start,end=p["source_span"]
            base["evidence_span"]=t["text"][start:end]
            base["utterance_sha256"]=sha(t["text"])
        else:
            base["utterance_sha256"]=sha(t["text"])
        records.append(base)
    # Do not silently discard unextracted utterances: report IDs and count only,
    # without implying this representation preserves their meanings.
    covered={p["source_turn"] for p in candidates}
    uncovered=[t["turn_id"] for t in memory["turns"] if t["turn_id"] not in covered]
    return {"version":VERSION,"mode":mode,"conversation_id":memory["conversation_id"],
       "source_turns":memory["last_turn"],"records":records,
       "uncovered_turn_ids":uncovered,"truth_state":"UNVERIFIED",
       "training_performed":False,"fact_promoted":False}

def compare(turns,unmatched_every=0):
    m=make_session(turns,unmatched_every)
    source_bytes=serialized_size(m)
    variants={}
    for mode in ("full","minimal","semantic_only"):
        doc=project(m,mode)
        count=len(doc["records"])
        variants[mode]={"bytes":serialized_size(doc),"candidate_records":count,
            "uncovered_turns":len(doc["uncovered_turn_ids"]),
            "has_full_utterance":mode=="full",
            "has_verbatim_evidence_span":mode in ("full","minimal"),
            "can_reconstruct_original_utterances":mode=="full" and not doc["uncovered_turn_ids"],
            "preserves_all_utterance_meanings":False,
            "approved_for_eviction":False}
    full_bytes=variants["full"]["bytes"]
    for mode,info in variants.items():
        info["bytes_vs_full"]=info["bytes"]-full_bytes
        info["ratio_vs_conversation"]=round(info["bytes"]/source_bytes,4)
        info["smaller_than_full"]=info["bytes"]<full_bytes
    return {"turns":turns,"unmatched_every":unmatched_every,
       "conversation_bytes":source_bytes,"variants":variants,
       "deletion_performed":False,"model_accuracy":None}

def benchmark(turn_counts=(100,500,1000),unmatched_every=0):
    return {"version":VERSION,"mode":"SYNTHETIC_EVIDENCE_PROJECTION_COMPARISON",
       "rows":[compare(n,unmatched_every) for n in turn_counts],
       "runtime_modified":False,"training_performed":False,"dry_run_only":True,
       "limitations":["Projected sizes are for standalone JSON representations, not the full v0.4.28.71 three-artifact pipeline.",
       "Minimal evidence is an extracted span, not sufficient proof of an entire utterance.",
       "Short utterances may yield larger minimal/semantic-only JSON than full evidence because of repeated SHA-256 metadata.",
       "Semantic-only hashes do not enable text reconstruction.",
       "Unmatched turns remain unrepresented; all replacement projections remain ineligible for eviction.",
       "No accuracy, recoverability or multi-writer consistency claims."]}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--turn-counts",nargs="+",type=int,default=[100,500,1000])
    p.add_argument("--unmatched-every",type=int,default=0)
    p.add_argument("--output",default="results/evidence_comparison_v042872.json")
    a=p.parse_args()
    if not a.turn_counts or any(n<1 for n in a.turn_counts):p.error("positive turn counts required")
    if a.unmatched_every<0:p.error("unmatched-every must be >=0")
    result=benchmark(a.turn_counts,a.unmatched_every)
    output=Path(a.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
