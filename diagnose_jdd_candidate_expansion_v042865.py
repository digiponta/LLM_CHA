#!/usr/bin/env python3
"""LLM_CHA v0.4.28.65: conservative speaker-scoped candidate expansion.
Research diagnostic only. No source utterances in reports, no automatic promotion.
Candidates are not verified. No anaphora or omitted-subject attribution.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path
from benchmark_jdd_speaker_aware_v042863 import balanced_rows, speaker_extract

VERSION="v0.4.28.65"
FIRST = r"(?:私|わたし|僕|俺|自分)"
SUBJ = rf"{FIRST}(?:は|も|が)?"
# Require explicit first-person reference and local predicate; do not infer
# whose assertion a third-person clause is.
PREFERENCE = re.compile(rf"{SUBJ}[^。！？\n]{{0,24}}?(?P<object>映画|音楽|旅行|読書|猫|犬)(?:が|は|を)?(?P<neg>好き(?:ではない|じゃない|でない)|嫌い)|"
                        rf"{SUBJ}[^。！？\n]{{0,24}}?(?P<positive_object>映画|音楽|旅行|読書|猫|犬)(?:が|は|を)?好き")
POSSESSION = re.compile(rf"{SUBJ}[^。！？\n]{{0,24}}?(?P<object>車|自転車|パソコン)(?:を|は|が)?持って"
                       rf"(?P<ending>いません|いない|ません|ない|います|いる|ます|る)")
TRAVEL = re.compile(rf"{SUBJ}[^。！？\n]{{0,24}}?(?P<object>東京|京都|大阪|北海道|沖縄)(?:に|へ)"
                   rf"(?P<ending>行きました|行った|行きます|行く)")
QUESTION = re.compile(r"[？?]|(?:ですか|ますか|でしょうか)[。！？]*$")
QUOTED = re.compile(r"[「」『』]")
HEARSAY = re.compile(r"と言っ|って言っ|だそう|らしい|と聞い")
CONDITIONAL = re.compile(r"もし|仮に|だったら|ならば|としたら")
NEG_TRAVEL = re.compile(r"行かな|行けな|行きません|行かない")
OBJECTS={"映画":"movie","音楽":"music","旅行":"travel","読書":"reading",
         "猫":"cat","犬":"dog","車":"car","自転車":"bicycle","パソコン":"computer",
         "東京":"tokyo","京都":"kyoto","大阪":"osaka","北海道":"hokkaido","沖縄":"okinawa"}

def expanded_candidates(cid, turn):
    speaker=turn.get("speaker")
    if speaker not in ("A","B"):raise ValueError("invalid speaker")
    txt=turn.get("text")
    tid=turn.get("turn_id")
    if not isinstance(txt,str) or not isinstance(tid,int) or tid<1:
        raise ValueError("invalid turn")
    # Sentence-wide safe abstention. Some valid facts will be rejected.
    guards=[]
    for name,pattern in (("question",QUESTION),("quotation",QUOTED),
                         ("hearsay",HEARSAY),("conditional",CONDITIONAL)):
        if pattern.search(txt):guards.append(name)
    if guards:return [], guards
    found=[]
    for rule,pattern in (("preference",PREFERENCE),("possession",POSSESSION),("travel",TRAVEL)):
        for m in pattern.finditer(txt):
            if rule=="preference":
                obj=m.group("object") or m.group("positive_object")
                polarity=not bool(m.group("neg"))
                predicate="likes"
            elif rule=="possession":
                obj=m.group("object");ending=m.group("ending")
                polarity=ending not in ("いません","いない","ません","ない")
                predicate="owns"
            else:
                obj=m.group("object")
                if NEG_TRAVEL.search(txt[m.end():m.end()+12]):continue
                polarity=True;predicate="visited_or_plans_visit"
            found.append({"conversation_id":cid,"speaker":speaker,"subject":speaker,
                "predicate":predicate,"object":OBJECTS[obj],"polarity":polarity,
                "source_turn":tid,"source_span":[m.start(),m.end()],
                "truth_state":"SPEAKER_REPORTED_UNVERIFIED","status":"candidate",
                "extractor":VERSION,"train_ready":False})
    return found, []

def benchmark(path,per_topic=20,seed=42863):
    rows,available=balanced_rows(path,per_topic,seed)
    if not rows:raise ValueError("no selected dialogues")
    counts=Counter();per_topic_counts={}
    for d in rows:
        local=Counter()
        for t in d["turns"]:
            old=speaker_extract(d["conversation_id"],t)
            new,guards=expanded_candidates(d["conversation_id"],t)
            local["utterances"]+=1
            local["baseline_candidates"]+=len(old)
            local["expanded_candidates"]+=len(new)
            local["expanded_matched_utterances"]+=bool(new)
            for g in guards:local["guard_"+g]+=1
        local["dialogues"]+=1
        counts.update(local)
        target=per_topic_counts.setdefault(d["topic_name"],Counter())
        target.update(local)
    return {"version":VERSION,"mode":"UNVERIFIED_EXPLICIT_SPEAKER_CANDIDATE_DIAGNOSTIC",
            "counts":dict(counts),
            "by_topic":{t:dict(x) for t,x in per_topic_counts.items()},
            "available_by_topic":available,
            "precision":None,"recall":None,"true_subject_resolution":False,
            "source_text_exported":False,"train_ready":False,"runtime_modified":False,
            "limitations":["Heuristic regex candidates are not semantic gold labels.",
                           "Sentence-wide guards deliberately cause false negatives.",
                           "No omitted-subject attribution or coreference resolution.",
                           "Visited/plans_visit is not yet temporally disambiguated.",
                           "Results are local research diagnostics, not training samples."]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--output",default="results/jdd_expanded_candidates_v042865.json")
    p.add_argument("--per-topic",type=int,default=20)
    p.add_argument("--seed",type=int,default=42863)
    a=p.parse_args()
    out=Path(a.output)
    if out.resolve()==Path(a.input).resolve():raise ValueError("refusing to overwrite input")
    report=benchmark(a.input,a.per_topic,a.seed)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
