#!/usr/bin/env python3
"""LLM_CHA v0.4.28.63: JDD speaker-aware, cautious semantic benchmark.

Local research use only. No JDD text output or training. Split A/B identities
remain session-scoped; direct first-person statements are the only candidates.
"""
import argparse
import hashlib
import json
from collections import Counter,defaultdict
from pathlib import Path
from semantic_extraction_v042858 import extract_candidates

VERSION="v0.4.28.63"
TOPICS=("Dailylife","School","Travel","Health","Entertainment")

def speaker_extract(conversation_id,turn):
    speaker=turn["speaker"]
    if speaker not in ("A","B"):raise ValueError("invalid speaker")
    text=turn["text"]
    # Reuse conservative source-anchored first-person rules without attributing
    # the person to the actual model user.
    found=extract_candidates(text,"user",turn["turn_id"])
    return [{**p,"subject":speaker,"speaker":speaker,
             "conversation_id":conversation_id,
             "truth_state":"SPEAKER_REPORTED_UNVERIFIED",
             "extractor":VERSION} for p in found]

def _stable_rank(seed,cid):
    return hashlib.sha256(f"{seed}:{cid}".encode()).hexdigest()

def balanced_rows(input_file,per_topic=20,seed=42863):
    if per_topic<1:raise ValueError("per_topic must be positive")
    groups=defaultdict(list);ids=set()
    with Path(input_file).open(encoding="utf-8") as stream:
        for n,line in enumerate(stream,1):
            if not line.strip():continue
            d=json.loads(line)
            cid=d.get("conversation_id")
            if not isinstance(cid,str) or not cid or cid in ids:
                raise ValueError(f"duplicate or missing conversation ID line {n}")
            ids.add(cid)
            if d.get("train_ready") is not False or d.get("original_speakers_preserved") is not True:
                raise ValueError(f"unsafe data line {n}")
            topic=d.get("topic_name")
            if topic in TOPICS:groups[topic].append(d)
    chosen=[]
    for topic in TOPICS:
        rows=sorted(groups[topic],key=lambda d:_stable_rank(seed,d["conversation_id"]))
        chosen.extend(rows[:per_topic])
    return chosen,{topic:len(groups[topic]) for topic in TOPICS}

def benchmark(input_file,per_topic=20,seed=42863):
    rows,available=balanced_rows(input_file,per_topic,seed)
    if not rows:raise ValueError("no usable conversations")
    counts=Counter();topics=Counter();relations=Counter();speakers=Counter()
    for d in rows:
        cid=d["conversation_id"];topics[d["topic_name"]]+=1
        counts["dialogues"]+=1
        turns=d.get("turns")
        if not isinstance(turns,list) or not turns:raise ValueError(f"empty turns in {cid}")
        evidence=[]
        for i,t in enumerate(turns,1):
            if t.get("turn_id")!=i or t.get("speaker") not in ("A","B") or not isinstance(t.get("text"),str) or not t["text"].strip():
                raise ValueError(f"bad turn in {cid}/{i}")
            counts["utterances"]+=1
            candidates=speaker_extract(cid,t)
            for p in candidates:
                if p["subject"]!=t["speaker"] or p["conversation_id"]!=cid or p["source_turn"]!=i:
                    raise ValueError("provenance leakage")
                evidence.append(p)
                relations[p["predicate"]+":"+p["object"]]+=1
                speakers[p["speaker"]]+=1
            if candidates:counts["utterances_with_candidates"]+=1
        counts["candidate_propositions"]+=len(evidence)
    counts["dialogues_with_candidates"]=sum(
        1 for d in rows if any(speaker_extract(d["conversation_id"],t) for t in d["turns"]))
    return {"version":VERSION,"mode":"JDD_SPEAKER_AWARE_RULE_BASELINE",
       "per_topic_requested":per_topic,"available_by_topic":available,
       "sampled_by_topic":dict(topics),"counts":dict(counts),
       "candidate_relation_counts":dict(relations),
       "candidate_speaker_counts":dict(speakers),
       "precision":None,"recall":None,"retrieval_accuracy":None,
       "human_verified":False,"train_ready":False,"runtime_modified":False,
       "source_speaker_isolation":True,"source_text_exported":False,
       "limitations":["Only explicitly matched first-person rules are extracted.",
          "Candidates are not verified facts; no pronoun/coreference resolution.",
          "Balanced sampling requires all five topics in the input split.",
          "No measured extraction precision/recall without human gold labels.",
          "Dialogues remain separate: no synthetic 1000-turn identity merging."]}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input",required=True)
    ap.add_argument("--per-topic",type=int,default=20)
    ap.add_argument("--seed",type=int,default=42863)
    ap.add_argument("--output",default="results/jdd_speaker_aware_v042863.json")
    a=ap.parse_args()
    out=Path(a.output)
    if out.resolve()==Path(a.input).resolve():raise ValueError("output equals input")
    result=benchmark(a.input,a.per_topic,a.seed)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
