#!/usr/bin/env python3
"""LLM_CHA v0.4.28.61 — Japanese Daily Dialogue local research adapter.

Source: https://github.com/jqk09a/japanese-daily-dialogue
CC BY-NC-ND 4.0 and dataset-specific no-redistribution/no-chatbot-service terms.
DO NOT commit source or derived dialogue text. Local evaluation use only.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

VERSION = "v0.4.28.61"
SOURCE = "https://github.com/jqk09a/japanese-daily-dialogue"
SPLITS = ("train","val","test")

def split_for(dialogue_id,seed=42861):
    digest=hashlib.sha256(f"{seed}:{dialogue_id}".encode()).digest()
    bucket=int.from_bytes(digest[:8],"big") % 100
    return "train" if bucket < 80 else "val" if bucket < 90 else "test"

def iter_dialogues(data):
    if isinstance(data,list):
        yield from data
    elif isinstance(data,dict):
        if "dialogues" in data and isinstance(data["dialogues"],list):
            yield from data["dialogues"]
        elif "utterances" in data:
            yield data
        else:
            raise ValueError("Unrecognized JSON object: expected dialogue or dialogues array")
    else:
        raise ValueError("Expected dialogue object or list")

def normalize(dialogue,source_filename,seed):
    if not isinstance(dialogue,dict):raise ValueError("Dialogue must be object")
    topic=dialogue.get("topic_name")
    topic_id=dialogue.get("topic_id")
    local_id=dialogue.get("dialogue_id")
    if not isinstance(topic,str) or not topic.strip():
        raise ValueError("Missing topic_name")
    if not isinstance(topic_id,int) or isinstance(topic_id,bool):
        raise ValueError("Missing topic_id")
    if not isinstance(local_id,(int,str)) or isinstance(local_id,bool) or str(local_id).strip()=="":
        raise ValueError("Missing dialogue_id")
    raw=dialogue.get("utterances")
    if not isinstance(raw,list) or len(raw)<2:raise ValueError("Need >=2 utterances")
    if dialogue.get("dialogue_length") is not None and dialogue["dialogue_length"]!=len(raw):
        raise ValueError("Declared length mismatch")
    turns=[]
    for expected,u in enumerate(raw,1):
        if not isinstance(u,dict) or u.get("turn_num")!=expected:
            raise ValueError("Turn numbering must be consecutive from 1")
        speaker=u.get("speaker")
        text=u.get("utterance")
        if speaker not in ("A","B") or not isinstance(text,str) or not text.strip():
            raise ValueError("Invalid speaker or empty utterance")
        turns.append({"turn_id":expected,"speaker":speaker,"text":text.strip()})
    identity=f"jdd-t{topic_id}-{local_id}"
    return {"conversation_id":identity,"source_dialogue_id":local_id,"topic_id":topic_id,
            "topic_name":topic,"source_file":source_filename,
            "split":split_for(identity,seed),"turns":turns,"source":SOURCE,
            "original_speakers_preserved":True,"synthetic_linking":False,
            "train_ready":False}

def convert_directory(source_dir,output_dir,seed=42861):
    src=Path(source_dir);dst=Path(output_dir)
    if not src.is_dir():raise FileNotFoundError(src)
    if src.resolve()==dst.resolve() or src.resolve() in dst.resolve().parents:
        raise ValueError("Output directory must be outside source directory")
    files=sorted(src.glob("*.json"))
    if not files:raise FileNotFoundError("No JSON in source directory")
    output={k:[] for k in SPLITS}
    ids=set();topics=Counter();turns=0
    for file in files:
        content=json.loads(file.read_text(encoding="utf-8-sig"))
        for d in iter_dialogues(content):
            row=normalize(d,file.name,seed)
            if row["conversation_id"] in ids:raise ValueError("Duplicate dialogue identity")
            ids.add(row["conversation_id"])
            topics[row["topic_name"]]+=1
            turns+=len(row["turns"])
            output[row["split"]].append(row)
    dst.mkdir(parents=True,exist_ok=True)
    # The output contains copyrighted utterances and MUST remain local.
    for split,rows in output.items():
        path=dst/f"jdd_{split}_v042861.jsonl"
        with path.open("w",encoding="utf-8") as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    manifest={"version":VERSION,"source":SOURCE,"dataset_license":"CC BY-NC-ND 4.0",
       "license_notes":"Research/evaluation only; no service use; no redistribution. Keep generated JSONL local.",
       "seed":seed,"dialogue_count":len(ids),"utterance_count":turns,
       "dialogues_per_split":{k:len(v) for k,v in output.items()},
       "topics":dict(topics),"human_verified":False,"train_ready":False,
       "runtime_modified":False,"source_files":[f.name for f in files]}
    (dst/"manifest_v042861.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",required=True,help="Locally cloned JDD data directory")
    p.add_argument("--output",default="data/jdd_local")
    p.add_argument("--seed",type=int,default=42861)
    a=p.parse_args()
    result=convert_directory(a.source,a.output,a.seed)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
