"""Read-only inspection of RealPersonaChat dialogue schema, without utterance text."""
import argparse,collections,json
from pathlib import Path

def shape(value):
    if isinstance(value,dict):return {"type":"dict","keys":list(value)[:25]}
    if isinstance(value,list):
        return {"type":"list","length":len(value),"first":shape(value[0]) if value else {"type":"empty"}}
    return {"type":type(value).__name__}

def inspect(source,limit=8):
    root=Path(source)
    dialogue_dir=root/"dialogues" if (root/"dialogues").is_dir() else root/"real_persona_chat"/"dialogues"
    if not dialogue_dir.is_dir():
        return {"status":"DIALOGUES_NOT_FOUND","source":str(root)}
    paths=sorted(dialogue_dir.glob("*.json"))
    samples=[]
    counts=collections.Counter()
    for path in paths[:limit]:
        try:
            data=json.loads(path.read_text(encoding="utf-8-sig"))
        except (UnicodeError,ValueError,OSError):
            counts["PARSE_ERROR"]+=1;continue
        utt=data.get("utterances")
        samples.append({"file":path.name,"utterances":shape(utt),
            "interlocutors":shape(data.get("interlocutors")),
            "evaluations":shape(data.get("evaluations"))})
        counts[type(utt).__name__]+=1
    return {"status":"SCHEMA_ONLY","file_count":len(paths),"sampled":len(samples),
            "samples":samples,"utterance_container_types":dict(counts),
            "raw_utterance_text_exported":False,"training_started":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="data-src/real-persona-chat")
    p.add_argument("--limit",type=int,default=8)
    p.add_argument("--output",default="results/real_persona_schema_v013588291.json")
    a=p.parse_args()
    if a.limit<1 or a.limit>50:raise ValueError("limit must be 1..50")
    report=inspect(a.source,a.limit)
    output=Path(a.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
