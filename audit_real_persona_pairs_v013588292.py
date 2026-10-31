"""Inspect RealPersonaChat turn pairing without exposing texts or training.

Use --export only after reviewing data license/privacy and persona mixing policy.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,re
from pathlib import Path

def split_for_dialogue(dialogue_id: str)->str:
    bucket=int(hashlib.sha256(("real-persona-split-v1:"+dialogue_id).encode()).hexdigest()[:8],16)%100
    return "train" if bucket<80 else "val" if bucket<90 else "test"

def find_dialogues(source):
    root=Path(source)
    for path in (root/"real_persona_chat"/"dialogues",root/"dialogues"):
        if path.is_dir():return path
    raise FileNotFoundError("Expected real_persona_chat/dialogues or dialogues under "+str(root))

def extract_pairs(doc):
    utterances=doc.get("utterances",[])
    people=doc.get("interlocutors",[])
    if not isinstance(utterances,list) or not isinstance(people,list) or len(people)!=2:
        return [],"BAD_DIALOGUE_SCHEMA"
    if not all(isinstance(u,dict) and isinstance(u.get("text"),str) and isinstance(u.get("interlocutor_id"),str) for u in utterances):
        return [],"BAD_UTTERANCE_SCHEMA"
    allowed=set(people)
    if len(allowed)!=2 or any(u["interlocutor_id"] not in allowed for u in utterances):
        return [],"BAD_SPEAKER_IDS"
    pairs=[]
    for prior,current in zip(utterances,utterances[1:]):
        if prior["interlocutor_id"]==current["interlocutor_id"]:continue
        user=prior["text"].strip();answer=current["text"].strip()
        if not user or not answer or len(user)>2000 or len(answer)>2000:continue
        pairs.append((user,answer,current["interlocutor_id"]))
    return pairs,None

def analyze(source,max_dialogues=0):
    folder=find_dialogues(source)
    files=sorted(folder.glob("*.json"))
    if max_dialogues:files=files[:max_dialogues]
    splits=collections.Counter();counts=collections.Counter();target_speakers=collections.Counter()
    samples=[]
    for path in files:
        try:doc=json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError,UnicodeError,ValueError):
            counts["PARSE_ERROR"]+=1;continue
        pairs,issue=extract_pairs(doc)
        if issue:counts[issue]+=1;continue
        identifier=str(doc.get("dialogue_id") or path.stem)
        split=split_for_dialogue(identifier)
        splits[split]+=1;counts["usable_pairs"]+=len(pairs)
        counts["valid_dialogues"]+=1
        for _,_,speaker in pairs:target_speakers[speaker]+=1
        if len(samples)<5:
            samples.append({"file":path.name,"split":split,"pairs":len(pairs),
                            "speaker_ids":list(doc["interlocutors"])})
    return {"status":"PAIR_AUDIT_ONLY","dialogue_files_checked":len(files),
        "counts":dict(counts),"dialogues_by_split":dict(splits),
        "top_target_speaker_ids":target_speakers.most_common(20),
        "sample_metadata":samples,"raw_text_exported":False,
        "training_started":False,
        "note":"Adjacent opposite-speaker utterances are only candidate pairs; persona target and license must be checked before training"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="data-src/real-persona-chat")
    p.add_argument("--max-dialogues",type=int,default=0)
    p.add_argument("--output",default="results/real_persona_pair_audit_v013588292.json")
    args=p.parse_args()
    if args.max_dialogues<0:raise ValueError("max-dialogues must be >=0")
    report=analyze(args.source,args.max_dialogues)
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
