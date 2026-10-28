"""Offline-only v0.13.58.10 data and replay readiness diagnostic.

No networking, no training, and no auto-approval. Reads approved local replay
JSONL or earlier generated text and any locally cached Wikipedia article JSON.
Reports readiness, leaks, and estimated token-scale balance. Never uses local
cached Wikipedia data for training automatically.
"""
import argparse,collections,hashlib,json,re
from pathlib import Path
from dialogue_format_v0135817 import dialogue_for

ROOT=Path(".")
INPUTS={
 "conversation": ("data/replay_conversation_approved_v013582.jsonl","data/replay_conversation_train.txt"),
 "knowledge": ("data/replay_knowledge_approved_v013582.jsonl",),
 "persona": ("data/replay_persona_approved_v013582.jsonl","data/replay_persona_train.txt"),
 "foundation": ("data/replay_foundation_train.txt","results/japanese_foundation_corpus_v01343/train.txt"),
 "literature": ("results/aozora_789_curated_v01353.txt",),
}
def normalized(s):return re.sub(r"\s+","",s.strip()).casefold()
def read_file(path):
    if path.suffix==".jsonl":
        items=[]
        for lineno,line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(),1):
            if not line.strip():continue
            try:obj=json.loads(line)
            except json.JSONDecodeError as exc:raise ValueError(f"{path}:{lineno}: malformed JSON") from exc
            if not isinstance(obj,dict):raise ValueError(f"{path}:{lineno}: not object")
            if obj.get("approved") is not True:raise ValueError(f"{path}:{lineno}: unapproved record")
            user=str(obj.get("user","")).strip();answer=str(obj.get("assistant","")).strip()
            if not user or not answer:raise ValueError(f"{path}:{lineno}: missing user/assistant")
            items.append(dialogue_for(user,answer))
        return items
    return [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
def choose_sources(base):
    resolved={}
    for domain,candidates in INPUTS.items():
        match=next((base/name for name in candidates if (base/name).is_file()),None)
        resolved[domain]=match
    return resolved
def audit(base,include_cache=False):
    found=choose_sources(base);details={};fingerprints={};conflicts=[]
    for domain,path in found.items():
        if path is None:
            details[domain]={"status":"MISSING","lines":0,"source":None};continue
        items=read_file(path)
        hashes=[hashlib.sha256(normalized(item).encode("utf-8")).hexdigest() for item in items]
        details[domain]={"status":"AVAILABLE","source":str(path),"lines":len(items),
                         "characters":sum(len(s) for s in items),
                         "unique_lines":len(set(hashes)),
                         "source_sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
        fingerprints[domain]=set(hashes)
    for first in fingerprints:
        for second in fingerprints:
            if first>=second:continue
            common=fingerprints[first]&fingerprints[second]
            if common:conflicts.append({"domains":[first,second],"exact_overlaps":len(common)})
    cache={"status":"NOT_CHECKED","files":0,"valid_articles":0}
    if include_cache:
        files=list((base/"results/wikipedia_curl_cache_v013589").glob("*.json"))
        valid=0
        for file in files:
            try:
                obj=json.loads(file.read_text(encoding="utf-8"))
                article=obj["article"]
                valid+=int(isinstance(article.get("id"),int) and isinstance(article.get("source"),str))
            except (OSError,ValueError,KeyError,TypeError):pass
        cache={"status":"INSPECTED_NOT_APPROVED","files":len(files),"valid_articles":valid}
    available={domain:x["lines"] for domain,x in details.items() if x["status"]=="AVAILABLE"}
    return {"version":"v0.13.58.10","mode":"OFFLINE_NO_NETWORK",
      "status":"AUDIT_COMPLETE","dataset":details,"overlap_warnings":conflicts,
      "local_wikipedia_cache":cache,"foundation_min_1000_met":available.get("foundation",0)>=1000,
      "can_train_literature_replay_40_30_20_10":False,
      "reason":"Readiness must be reassessed under trainer-specific minimums and repetition cap; no training or promotion performed.",
      "training_performed":False,"training_approved":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--include-cache",action="store_true")
    p.add_argument("--output",type=Path,default=Path("results/offline_replay_audit_v0135810.json"))
    args=p.parse_args()
    result=audit(args.root,args.include_cache)
    dest=args.root/args.output
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"status":result["status"],"network":"DISABLED",
        "counts":{d:v["lines"] for d,v in result["dataset"].items()},
        "overlap_warnings":result["overlap_warnings"],
        "foundation_min_1000_met":result["foundation_min_1000_met"],
        "cache":result["local_wikipedia_cache"],"training_approved":False},ensure_ascii=False))
    print("report:",dest)
if __name__=="__main__":main()
