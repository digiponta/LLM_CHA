"""RealPersonaChat 5k pair pilot. Read-only by default; explicit opt-in export.

Target only one speaker's replies; train-split dialogues only. Not a privacy
guarantee: manually audit records before using exported data to train.
"""
import argparse,collections,hashlib,json,re
from pathlib import Path
from audit_real_persona_pairs_v013588292 import find_dialogues,extract_pairs,split_for_dialogue

PII=re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|https?://\S+|(?:\+?81[- ]?)?0\d{1,4}[- ]\d{1,4}[- ]\d{3,4}")
JP=re.compile(r"[ぁ-んァ-ヶ一-龠]")
def norm(s):return "".join(s.split()).strip("。！？?!、.,")
def holdout_strings(path):
    data=json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return {norm(c[k]) for c in data["cases"] for k in ("question","example_acceptable") if c.get(k)}
def eligible(user,assistant,blocked):
    if not (2<=len(user)<=240 and 2<=len(assistant)<=240):return "LENGTH"
    if PII.search(user) or PII.search(assistant):return "PII_HEURISTIC"
    if not JP.search(user) or not JP.search(assistant):return "NON_JAPANESE"
    if norm(user) in blocked or norm(assistant) in blocked:return "EXACT_HOLDOUT"
    return None
def build(source,target,holdout,max_pairs=5000):
    if not target:raise ValueError("TARGET_SPEAKER_REQUIRED")
    blocked=holdout_strings(holdout);counts=collections.Counter();seen=set();rows=[];dialogues=set()
    for f in sorted(find_dialogues(source).glob("*.json")):
        doc=json.loads(f.read_text(encoding="utf-8-sig"))
        identifier=str(doc.get("dialogue_id") or f.stem)
        if split_for_dialogue(identifier)!="train":continue
        pairs,error=extract_pairs(doc)
        if error:counts[error]+=1;continue
        for user,answer,reply_speaker in pairs:
            if reply_speaker!=target:continue
            counts["speaker_target_pairs"]+=1
            bad=eligible(user,answer,blocked)
            if bad:counts[bad]+=1;continue
            key=hashlib.sha256((norm(user)+"\n"+norm(answer)).encode()).hexdigest()
            if key in seen:counts["DUPLICATE"]+=1;continue
            seen.add(key)
            rows.append({"user":user,"assistant":answer,"source":"chat-manual"})
            dialogues.add(identifier)
            if len(rows)>=max_pairs:break
        if len(rows)>=max_pairs:break
    return rows,{"status":"PILOT_CANDIDATE_REVIEW_REQUIRED","target_speaker":target,
      "candidate_pairs":len(rows),"dialogues_used":len(dialogues),
      "rejections":dict(counts),"split":"train-only","holdout_exact_excluded":True,
      "semantic_holdout_independence_verified":False,"pii_absence_verified":False,
      "license_verified_by_tool":False,"model_trained":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="data-src/real-persona-chat")
    p.add_argument("--target-speaker",required=True)
    p.add_argument("--holdout",default="data/daily_conversation_eval_v013588283.json")
    p.add_argument("--max-pairs",type=int,default=5000)
    p.add_argument("--report",default="results/real_persona_pilot_v013588293.json")
    p.add_argument("--export",action="store_true")
    p.add_argument("--license-reviewed",action="store_true")
    p.add_argument("--output",default="data/real_persona_pilot_v013588293.jsonl")
    a=p.parse_args()
    if not 1<=a.max_pairs<=5000:raise ValueError("max-pairs must be 1..5000")
    if a.export and not a.license_reviewed:raise ValueError("LICENSE_REVIEW_REQUIRED")
    rows,report=build(a.source,a.target_speaker,a.holdout,a.max_pairs)
    report["exported"]=bool(a.export)
    if a.export:
        if not rows:raise ValueError("NO_ELIGIBLE_PAIRS")
        dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():raise FileExistsError("Refusing to overwrite existing pilot: "+str(dest))
        with dest.open("x",encoding="utf-8") as handle:
            for row in rows:handle.write(json.dumps(row,ensure_ascii=False)+"\n")
    dest=Path(a.report);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
