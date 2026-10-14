#!/usr/bin/env python3
"""LLM_CHA v0.4.28.64 — privacy-preserving JDD extraction diagnostics.

Aggregate counts only; no copyrighted dialogue strings in reports.
Heuristic categories overlap and are NOT syntactic gold labels.
"""
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from benchmark_jdd_speaker_aware_v042863 import balanced_rows, speaker_extract, TOPICS

VERSION="v0.4.28.64"
PATTERNS={
 "first_person_explicit":re.compile(r"私|僕|わたし|自分|俺"),
 "subject_marker":re.compile(r"は|が"),
 "question":re.compile(r"[？?]|(?:ですか|ますか|でしょうか|かな)[。！？?]*$"),
 "negation":re.compile(r"ない|ません|ずに|ではない|じゃない"),
 "preference_lexeme":re.compile(r"好き|嫌い|好み|楽しい"),
 "possession_lexeme":re.compile(r"持っ|所有|買っ|購入"),
 "travel_lexeme":re.compile(r"行く|行き|旅行|電車|バス|駅"),
 "request_lexeme":re.compile(r"ください|お願い|してもら|してくれ"),
 "reported_speech":re.compile(r"って言|と言|そうです|らしい|聞いた"),
 "quotation_marks":re.compile(r"[「」『』]"),
}
def diagnose(input_path,per_topic=20,seed=42863):
 rows,available=balanced_rows(input_path,per_topic,seed)
 if not rows:raise ValueError("no sampled conversations")
 total=Counter();by_topic=defaultdict(Counter)
 for d in rows:
  topic=d["topic_name"];total["dialogues"]+=1;by_topic[topic]["dialogues"]+=1
  for i,turn in enumerate(d["turns"],1):
   if turn.get("turn_id")!=i or turn.get("speaker") not in ("A","B") or not isinstance(turn.get("text"),str):
    raise ValueError("malformed turn")
   text=turn["text"]
   flags={name:bool(p.search(text)) for name,p in PATTERNS.items()}
   extracted=speaker_extract(d["conversation_id"],turn)
   for ctr in (total,by_topic[topic]):
    ctr["utterances"]+=1
    if extracted:
     ctr["matched_utterances"]+=1
     ctr["candidate_propositions"]+=len(extracted)
    else:ctr["unmatched_utterances"]+=1
    for name,hit in flags.items():
     if hit:ctr["feature_"+name]+=1
     if hit and not extracted:ctr["unmatched_feature_"+name]+=1
    if not extracted and not any(flags.values()):ctr["unmatched_no_feature_hit"]+=1
    if not extracted and flags["question"]:ctr["unmatched_question_like"]+=1
    if not extracted and flags["reported_speech"]:ctr["unmatched_reported_speech_like"]+=1
    if not extracted and flags["first_person_explicit"]:ctr["unmatched_explicit_first_person"]+=1
    if not extracted and not flags["first_person_explicit"]:ctr["unmatched_without_explicit_first_person"]+=1
 return {"version":VERSION,"mode":"AGGREGATE_JDD_EXTRACTION_DIAGNOSTIC",
    "sampled_by_topic":{t:by_topic[t]["dialogues"] for t in TOPICS},
    "available_by_topic":available,"totals":dict(total),
    "features_by_topic":{t:dict(by_topic[t]) for t in TOPICS},
    "extraction_precision":None,"extraction_recall":None,
    "train_ready":False,"runtime_modified":False,
    "source_text_exported":False,"heuristic_categories_can_overlap":True,
    "interpretation":"Pattern hits are candidates for rule coverage analysis, not confirmed semantic structures."}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--input",required=True)
 p.add_argument("--per-topic",type=int,default=20)
 p.add_argument("--seed",type=int,default=42863)
 p.add_argument("--output",default="results/jdd_extraction_diagnostic_v042864.json")
 a=p.parse_args()
 output=Path(a.output)
 if output.resolve()==Path(a.input).resolve():raise ValueError("output and input must differ")
 report=diagnose(a.input,a.per_topic,a.seed)
 output.parent.mkdir(parents=True,exist_ok=True)
 output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
