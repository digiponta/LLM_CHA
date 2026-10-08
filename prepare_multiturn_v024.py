"""RealPersonaChat -> chat.py-compatible multi-turn SFT examples.

SFT 'user' is an already formatted prompt body ending in the newest '人: ...'.
The trainer adds '\nAI:'; earlier assistant responses stay in the prompt.
Conversation-wise split follows the existing converter.
"""
from __future__ import annotations
import argparse, json, random
from pathlib import Path
from prepare_realpersonachat_v020 import split_for

def pairs(dialogue, history_turns=2):
    rows=dialogue.get("utterances",[])
    for i in range(1,len(rows)):
        prev,cur=rows[i-1],rows[i]
        if not isinstance(prev,dict) or not isinstance(cur,dict):continue
        if prev.get("interlocutor_id")==cur.get("interlocutor_id"):continue
        answer=cur.get("text","")
        if not isinstance(answer,str) or not answer.strip() or len(answer)>250:continue
        # Perspective: speaker of current utterance is AI; all other speakers are '人'.
        prior=rows[max(0,i-(2*history_turns+1)):i]
        lines=[]
        valid=True
        for entry in prior:
            if not isinstance(entry,dict) or not isinstance(entry.get("text"),str):
                valid=False;break
            msg=entry["text"].strip()
            if not msg or len(msg)>250 or any(v in msg for v in ("＊＊","\n人:","\nAI:")):
                valid=False;break
            role="AI" if entry.get("interlocutor_id")==cur.get("interlocutor_id") else "人"
            lines.append((role,msg))
        if not valid or not lines or lines[-1][0]!="人":continue
        if "＊＊" in answer or "\n人:" in answer or "\nAI:" in answer:continue
        # Require strict alternation to match chat.py's history format.
        if any(a[0]==b[0] for a,b in zip(lines,lines[1:])):continue
        yield {"user":"\n".join(f"{role}: {msg}" for role,msg in lines),
               "assistant":answer.strip()}

def convert(src:Path,out:Path,max_dialogues=1000,history_turns=2,seed=42):
    files=sorted(src.glob("*.json"))
    if not files:raise FileNotFoundError(f"No JSON dialogues at {src}")
    rng=random.Random(seed)
    rng.shuffle(files)
    if max_dialogues>0:files=files[:max_dialogues]
    out.mkdir(parents=True,exist_ok=True)
    counts={k:0 for k in ("train","val","test")}
    handles={k:(out/f"rpc_multiturn_{k}.jsonl").open("w",encoding="utf-8") for k in counts}
    seen=set()
    try:
        for path in files:
            dialogue=json.loads(path.read_text(encoding="utf-8"))
            split=split_for(str(dialogue.get("dialogue_id",path.stem)))
            for row in pairs(dialogue,history_turns):
                # Duplicate pairs across groups are skipped; avoid leakage.
                key=(row["user"],row["assistant"])
                if key in seen:continue
                seen.add(key)
                handles[split].write(json.dumps(row,ensure_ascii=False)+"\n")
                counts[split]+=1
    finally:
        for handle in handles.values():handle.close()
    (out/"rpc_multiturn_manifest.json").write_text(json.dumps(
        {"pairs":counts,"history_turns":history_turns,"max_dialogues":max_dialogues,
         "format":"preformatted_prompts","seed":seed},indent=2)+"\n",encoding="utf-8")
    return counts

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dialogues",type=Path,default=Path("data-src/real-persona-chat/real_persona_chat/dialogues"))
    p.add_argument("--output",type=Path,default=Path("data/realpersonachat_multiturn"))
    p.add_argument("--max-dialogues",type=int,default=1000)
    p.add_argument("--history-turns",type=int,default=2)
    p.add_argument("--seed",type=int,default=42)
    a=p.parse_args()
    if a.history_turns<1: p.error("history-turns must be positive")
    print(convert(a.dialogues,a.output,a.max_dialogues,a.history_turns,a.seed))
if __name__=="__main__": main()
