"""v0.2.12 broad dialogue training set, isolated from the synthetic v0.2.11 pilot.

Inputs come from v0.2.4's dialogue-disjoint RealPersonaChat splits.
A deterministic, explicit topic holdout additionally removes tagged topics from training.
Data source license/attribution remains as documented for RealPersonaChat.
"""
from __future__ import annotations
import argparse,hashlib,json,random,re
from collections import Counter
from pathlib import Path
from conversation_diagnostics_v026 import classify_quality

TOPICS={
 "photo":("写真","撮影","カメラ","夜景","photograph","camera","photo"),
 "garden":("庭","園芸","植物","ハーブ","ミント","garden","plant","herb"),
}
def row_topic(row):
    text=(row["user"]+" "+row["assistant"]).lower()
    return {label for label,words in TOPICS.items() if any(w in text for w in words)}
def clean(row):
    if not isinstance(row,dict):return False
    u,a=row.get("user"),row.get("assistant")
    if not isinstance(u,str) or not isinstance(a,str):return False
    if not u.startswith("人: ") or "\nAI:" not in u and "\n" in u:return False
    if not 8<=len(a.strip())<=250:return False
    if "\n人:" in a or "\nAI:" in a or "＊＊" in a:return False
    return not classify_quality(u.split("人: ")[-1],a)["generic"]
def load(path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():yield json.loads(line)
def key(row):
    return hashlib.sha256((row["user"]+"\x00"+row["assistant"]).encode("utf-8")).hexdigest()
def prepare(src:Path,dst:Path,*,max_train=50000,seed=42):
    rng=random.Random(seed)
    splits={name:list(load(src/f"rpc_multiturn_{name}.jsonl")) for name in ("train","val","test")}
    out={};counts=Counter()
    # Never move records from val/test into train.
    for name,rows in splits.items():
        eligible=[]
        for row in rows:
            if not clean(row):counts[f"{name}_filtered"]+=1;continue
            topic=row_topic(row)
            if name=="train" and topic:
                counts["train_topic_excluded"]+=1;continue
            if name=="val" and topic:
                # Explicit topic holdout is separate from ordinary val.
                eligible.append((row,True));continue
            eligible.append((row,False))
        if name=="train":
            rng.shuffle(eligible);eligible=eligible[:max_train]
        out[name]=[row for row,flag in eligible if not flag]
        if name=="val":out["topic_holdout"]=[row for row,flag in eligible if flag]
    # Remove exact duplicate prompts and targets between output groups.
    seen=set()
    for name in ("train","val","topic_holdout","test"):
        unique=[]
        for row in out[name]:
            k=key(row)
            if k in seen:counts["duplicate_removed"]+=1;continue
            seen.add(k);unique.append(row)
        out[name]=unique
    if not out["train"] or not out["val"]:raise ValueError("Train and validation must both be nonempty")
    dst.mkdir(parents=True,exist_ok=True)
    for name,rows in out.items():
        with (dst/f"{name}.jsonl").open("w",encoding="utf-8") as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    manifest={"counts":{k:len(v) for k,v in out.items()},"filters":dict(counts),
              "topic_holdout_keywords":TOPICS,"max_train":max_train,"seed":seed,
              "warning":"topic separation is keyword-based, not semantic topic isolation; validate manually"}
    (dst/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("data/realpersonachat_multiturn"))
    p.add_argument("--output",type=Path,default=Path("data/dialogue_generalization_v0212"))
    p.add_argument("--max-train",type=int,default=50000)
    p.add_argument("--seed",type=int,default=42)
    a=p.parse_args()
    print(json.dumps(prepare(a.source,a.output,max_train=a.max_train,seed=a.seed),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
