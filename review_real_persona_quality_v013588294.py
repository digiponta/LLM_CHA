"""Local, privacy-conscious CP pilot review; no training and no plaintext export by default."""
import argparse,collections,hashlib,json,random,re
from pathlib import Path
from audit_real_persona_pairs_v013588292 import find_dialogues,extract_pairs,split_for_dialogue
from prepare_real_persona_pilot_v013588293 import eligible,holdout_strings,norm

def profile_metadata(source,speaker):
    root=Path(source)
    candidates=[root/"real_persona_chat"/"interlocutors.json",root/"interlocutors.json"]
    for f in candidates:
        if f.is_file():
            data=json.loads(f.read_text(encoding="utf-8-sig"))
            if not isinstance(data,dict):return {"status":"BAD_PROFILES_FORMAT"}
            obj=data.get(speaker)
            if obj is None:return {"status":"SPEAKER_NOT_IN_PROFILES"}
            if isinstance(obj,dict):
                return {"status":"PROFILE_FOUND","field_names":list(obj.keys()),"field_types":{k:type(v).__name__ for k,v in obj.items()}}
            return {"status":"PROFILE_FOUND","value_type":type(obj).__name__}
    return {"status":"PROFILES_FILE_NOT_FOUND"}

def review(source,speaker,max_examples=12):
    blocked=holdout_strings("data/daily_conversation_eval_v013588283.json")
    items=[];seen=set();counts=collections.Counter()
    for f in sorted(find_dialogues(source).glob("*.json")):
        doc=json.loads(f.read_text(encoding="utf-8-sig"))
        if split_for_dialogue(str(doc.get("dialogue_id") or f.stem))!="train":continue
        pairs,issue=extract_pairs(doc)
        if issue:counts[issue]+=1;continue
        for user,assistant,answer_speaker in pairs:
            if answer_speaker!=speaker:continue
            reason=eligible(user,assistant,blocked)
            if reason:counts[reason]+=1;continue
            fingerprint=hashlib.sha256((norm(user)+"\n"+norm(assistant)).encode("utf-8")).hexdigest()
            if fingerprint in seen:counts["DUPLICATE"]+=1;continue
            seen.add(fingerprint)
            counts["accepted"]+=1
            items.append({"pair_hash":fingerprint[:16],"dialogue_id":str(doc.get("dialogue_id") or f.stem),
                          "user_chars":len(user),"assistant_chars":len(assistant),
                          "user":user,"assistant":assistant})
    rng=random.Random(42)
    selected=rng.sample(items,min(max_examples,len(items)))
    # Default report contains only schema and metrics. Text stays local and is displayed ONLY on explicit --show-text.
    out={"status":"HUMAN_REVIEW_REQUIRED","speaker_id":speaker,"profile":profile_metadata(source,speaker),
         "counts":dict(counts),"sample_count":len(selected),
         "samples":[{k:v for k,v in item.items() if k not in ("user","assistant")} for item in selected],
         "raw_text_exported":False,"license_verified":False,"training_started":False}
    return out,selected

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="data-src/real-persona-chat")
    p.add_argument("--target-speaker",default="CP")
    p.add_argument("--samples",type=int,default=12)
    p.add_argument("--show-text",action="store_true",help="Print sensitive dialogue snippets locally, not in saved report")
    p.add_argument("--output",default="results/real_persona_quality_review_v013588294.json")
    a=p.parse_args()
    if not 1<=a.samples<=30:raise ValueError("samples 1..30")
    result,selected=review(a.source,a.target_speaker,a.samples)
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if a.show_text:
        print("\nLOCAL_ONLY_EXAMPLES (do not upload unredacted):")
        for x in selected:print(json.dumps({"pair_hash":x["pair_hash"],"user":x["user"],"assistant":x["assistant"]},ensure_ascii=False))
if __name__=="__main__":main()
