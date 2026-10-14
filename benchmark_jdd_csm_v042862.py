#!/usr/bin/env python3
"""LLM_CHA v0.4.28.62 — local JDD session-isolated CSM benchmark.

A/B are source speakers, NOT user/assistant roles. No first-person facts are
assigned to the real user. Only aggregate metrics leave the local evaluation.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
from conversation_semantic_memory_v042857 import new_memory,keyword_candidates

VERSION="v0.4.28.62"

def evaluate(input_path,limit=None,recent_limit=5):
    if limit is not None and limit<1:raise ValueError("limit must be positive")
    if recent_limit<1:raise ValueError("recent_limit must be positive")
    counts=Counter();topics=Counter();seen=set()
    for number,line in enumerate(Path(input_path).open(encoding="utf-8"),1):
        if not line.strip():continue
        if limit is not None and counts["dialogues"]>=limit:break
        d=json.loads(line)
        if d.get("train_ready") is not False or d.get("original_speakers_preserved") is not True:
            raise ValueError(f"unsafe input row {number}")
        cid=d.get("conversation_id")
        if not isinstance(cid,str) or not cid or cid in seen:
            raise ValueError(f"missing/duplicate session ID: {number}")
        seen.add(cid)
        turns=d.get("turns")
        if not isinstance(turns,list) or not turns:raise ValueError(f"invalid turns: {number}")
        memory=new_memory(cid)
        memory["source_speakers"]=["A","B"]
        for i,t in enumerate(turns,1):
            if t.get("turn_id")!=i or t.get("speaker") not in ("A","B") or not isinstance(t.get("text"),str) or not t["text"].strip():
                raise ValueError(f"invalid turn: {number}/{i}")
            # Store original speaker role and source: never interpret as user's identity.
            utterance=t["text"].strip()
            hits=keyword_candidates(utterance)
            for word in hits:
                if word not in memory["keywords"]:memory["keywords"].append(word)
            if hits:memory["current_topic"]=hits[0]
            memory["recent_turns"].append({"turn_id":i,"role":t["speaker"],"text":utterance})
            memory["recent_turns"]=memory["recent_turns"][-recent_limit:]
            memory["last_turn"]=i
            counts["utterances"]+=1
            counts["keyword_hits"]+=len(hits)
            counts["full_history_chars"]+=len(utterance)
        counts["dialogues"]+=1
        counts["distinct_keywords_total"]+=len(memory["keywords"])
        counts["recent_context_chars"]+=sum(len(t["text"]) for t in memory["recent_turns"])
        topics[str(d.get("topic_name","unknown"))]+=1
        # All propositions remain empty until speaker-aware extractor exists.
        if memory["propositions"] or memory["train_ready"] is not False:
            raise ValueError("unsafe user-fact attribution")
    return {"version":VERSION,"mode":"JDD_CONVERSATION_MEMORY_BASELINE",
        "counts":dict(counts),"topics":dict(topics),
        "source_speakers_preserved":True,"cross_conversation_memory_merging":False,
        "speaker_aware_proposition_extraction":False,
        "semantic_retrieval_recall":None,"model_response_quality":None,
        "measured_context_tokens":None,
        "human_verified":False,"train_ready":False,"runtime_modified":False,
        "limitations":["Keyword extraction is a fixed-term baseline only.",
          "Character counts are not token counts and do not measure actual inference prompt size.",
          "Original A/B speakers cannot be mapped to the real user or assistant.",
          "No cross-dialogue synthetic long conversation is constructed.",
          "No Semantic fact recall accuracy is claimed."]}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input",required=True)
    ap.add_argument("--output",default="results/jdd_csm_benchmark_v042862.json")
    ap.add_argument("--limit",type=int)
    ap.add_argument("--recent-limit",type=int,default=5)
    a=ap.parse_args()
    result=evaluate(a.input,a.limit,a.recent_limit)
    p=Path(a.output)
    if p.resolve()==Path(a.input).resolve():raise ValueError("output/input must differ")
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
