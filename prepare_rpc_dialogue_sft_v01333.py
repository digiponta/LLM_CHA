"""v0.13.33 convert RealPersonaChat dialogues to isolated dialogue-SFT JSONL.

Do not mix utterances from different dialogues. Splits are hash-stable per
dialogue_id, never per utterance. No source files are modified.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

def split_id(dialogue_id,seed="rpc-v01333",train=0.9,val=0.05):
    n=int.from_bytes(hashlib.sha256(f"{seed}:{dialogue_id}".encode()).digest()[:8],"big")/2**64
    return "train" if n<train else ("val" if n<train+val else "test")

def validate_dialogue(obj):
    if not isinstance(obj,dict) or not isinstance(obj.get("utterances"),list):
        raise ValueError("missing utterances")
    did=obj.get("dialogue_id")
    if did is None:raise ValueError("missing dialogue_id")
    seen=set()
    utterances=[]
    for record in obj["utterances"]:
        if not isinstance(record,dict):raise ValueError("invalid utterance")
        uid=record.get("utterance_id")
        speaker=record.get("interlocutor_id")
        message=record.get("text")
        if not isinstance(uid,int) or uid in seen:raise ValueError("duplicate or invalid utterance_id")
        seen.add(uid)
        if not isinstance(speaker,str) or not speaker.strip() or not isinstance(message,str):
            raise ValueError("missing speaker or text")
        if message.strip():utterances.append((uid,speaker,message.strip()))
    utterances.sort(key=lambda x:x[0])
    if len({s for _,s,_ in utterances})>2:raise ValueError("more than two speakers")
    return did,utterances

def extract(obj,history=4):
    if history<0:raise ValueError("history must be nonnegative")
    did,utterances=validate_dialogue(obj)
    examples=[]
    for i in range(1,len(utterances)):
        if utterances[i][1]==utterances[i-1][1]:continue
        prior=utterances[max(0,i-history-1):i]
        if not prior:continue
        # Speaker-relative labels, not real identities or asserted Nagato persona.
        target_speaker=utterances[i][1]
        context="\n".join(("相手: " if s!=target_speaker else "自分: ")+text for _,s,text in prior)
        # Most recent opposite-speaker utterance always included.
        examples.append({"user":context,"assistant":utterances[i][2],
                         "source":"rpc-dialogue-sft",
                         "dialogue_id":did,"utterance_id":utterances[i][0],
                         "role_style":"SPEAKER_RELATIVE",
                         "approval_state":"UNAPPROVED","truth_state":"UNVERIFIED"})
    return examples

def prepare(input_dir,output_dir,history=4,limit=0):
    paths=sorted(input_dir.glob("*.json"))
    if limit>0:paths=paths[:limit]
    if not paths:raise ValueError("no dialogue JSON files found")
    files={name:[] for name in ("train","val","test")}
    counts=Counter();errors=[]
    ids=set()
    for path in paths:
        try:
            obj=json.loads(path.read_text(encoding="utf-8-sig"))
            did,records=validate_dialogue(obj)
            if did in ids:raise ValueError("duplicate dialogue_id")
            ids.add(did)
            items=extract(obj,history=history)
            split=split_id(did)
            files[split].extend(items)
            counts[split+"_dialogues"]+=1
            counts[split+"_pairs"]+=len(items)
        except (ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
            errors.append({"file":path.name,"error":str(exc)})
    if not any(files.values()):raise ValueError("no valid pairs")
    output_dir.mkdir(parents=True,exist_ok=True)
    for name,rows in files.items():
        path=output_dir/f"rpc_sft_{name}_v01333.jsonl"
        if path.exists():raise FileExistsError(f"output already exists: {path}")
    manifest=output_dir/"rpc_sft_manifest_v01333.json"
    if manifest.exists():raise FileExistsError(str(manifest))
    for name,rows in files.items():
        (output_dir/f"rpc_sft_{name}_v01333.jsonl").write_text(
            "".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows),encoding="utf-8")
    report={"version":"v0.13.33","input_files":len(paths),"history":history,
            "counts":dict(counts),"errors_count":len(errors),"errors_sample":errors[:50],
            "split":"sha256(dialogue_id), train90 val5 test5",
            "no_training_or_promotion":True}
    manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,default=Path("data-src/real-persona-chat/real_persona_chat/dialogues"))
    p.add_argument("--output",type=Path,default=Path("results/rpc_sft_v01333"))
    p.add_argument("--history",type=int,default=4)
    p.add_argument("--limit",type=int,default=0,help="0 means all JSON files")
    a=p.parse_args()
    if a.history<0 or a.limit<0:p.error("history/limit must be nonnegative")
    print(json.dumps(prepare(a.input,a.output,a.history,a.limit),ensure_ascii=False,indent=2))

if __name__=="__main__":main()
