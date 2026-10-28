"""v0.13.58.23: offline token-measured W/WR/WRP experimental mixture staging.

No model load, training, approval, or promotion. Validation is never sampled.
Each sample includes a next-token supervision mask, preserving assistant-only
loss for dialogue/persona and full LM loss for Wikipedia.
"""
import argparse,collections,hashlib,json,random
from pathlib import Path
from audit_offline_replay_v0135810 import read_file
from dialogue_format_v0135817 import split_dialogue

PLANS={"W":{"wiki":1.0},"WR":{"wiki":0.7,"conversation":0.3},
       "WRP":{"wiki":0.6,"conversation":0.3,"persona":0.1}}

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def dialogue_chunks(text,tok,context,domain,source_index):
    prompt,answer=split_dialogue(text)
    prefix=tok.encode(prompt,add_bos=True)
    continuation=tok.encode(answer,add_bos=False,add_eos=True)
    ids=prefix+continuation
    for start in range(0,len(ids)-1,context):
        seq=ids[start:start+context+1]
        if len(seq)<2:continue
        # target at absolute token position start+j+1
        mask=[int(start+j+1>=len(prefix)) for j in range(len(seq)-1)]
        if not any(mask):continue
        yield {"domain":domain,"source_index":source_index,"token_ids":seq,
               "loss_mask":mask,"supervised_tokens":sum(mask),
               "approval":"EXPERIMENT_CANDIDATE_ONLY"}

def wiki_chunks(path):
    with path.open(encoding="utf-8-sig") as f:
        for idx,line in enumerate(f,1):
            if not line.strip():continue
            obj=json.loads(line)
            seq=obj["token_ids"]
            if obj.get("approval")!="PENDING_REVIEW" or obj.get("auto_promote") is not False:
                raise ValueError("wiki approval state invalid")
            yield {"domain":"wiki","source_index":idx,"article_id":obj["article_id"],
                   "title":obj["title"],"url":obj["url"],"token_ids":seq,
                   "loss_mask":[1]*(len(seq)-1),"supervised_tokens":len(seq)-1,
                   "approval":"EXPERIMENT_CANDIDATE_ONLY"}

def build(dataset_dir,tokenizer_path,conversation,persona,output_dir,budget=30000,context=512,seed=135823,max_reuse=8):
    if output_dir.exists():raise FileExistsError(output_dir)
    if budget<1 or not 2<=context<=512 or max_reuse<1:raise ValueError("invalid settings")
    manifest=json.loads((dataset_dir/"manifest.json").read_text(encoding="utf-8-sig"))
    if manifest.get("status")!="STAGED_NOT_APPROVED":raise ValueError("invalid staged manifest")
    if digest(tokenizer_path)!=manifest.get("tokenizer_sha256"):raise ValueError("tokenizer mismatch")
    wiki_path=dataset_dir/"train_chunks.jsonl"
    val_path=dataset_dir/"validation_chunks.jsonl"
    for p in (wiki_path,val_path):
        if digest(p)!=manifest["file_sha256"][p.name]:raise ValueError("dataset hash mismatch: "+p.name)
    if context<manifest["max_context_tokens"]:raise ValueError("context smaller than prepared chunks")
    from tokenizer_bpe import Tokenizer
    tok=Tokenizer.load(str(tokenizer_path))
    pools={"wiki":list(wiki_chunks(wiki_path))}
    sources={}
    for domain,path in (("conversation",conversation),("persona",persona)):
        if not path.is_file():raise FileNotFoundError(path)
        lines=read_file(path)  # approved dialogue JSONL required
        pools[domain]=[chunk for i,line in enumerate(lines) for chunk in dialogue_chunks(line,tok,context,domain,i)]
        if not pools[domain]:raise ValueError("no usable replay examples: "+domain)
        sources[domain]={"sha256":digest(path),"records":len(lines),"chunks":len(pools[domain])}
    for domain,rows in pools.items():
        for row in rows:
            seq=row["token_ids"]
            if len(seq)<2 or len(seq)>context+1 or len(row["loss_mask"])!=len(seq)-1:
                raise ValueError("invalid chunk: "+domain)
            if not all(type(x)==int and x>=0 for x in seq):raise ValueError("bad token ID")
    all_rows={};summaries={}
    for name,weights in PLANS.items():
        rng=random.Random(seed)
        selections=[];counts=collections.Counter();used=collections.Counter()
        for domain,weight in weights.items():
            pool=pools[domain][:]
            rng.shuffle(pool)
            target=round(budget*weight)
            available=len(pool)* (1 if domain=="wiki" else max_reuse)
            idx=0
            while counts[domain]<target and idx<available:
                row=pool[idx%len(pool)]
                repetitions=idx//len(pool)
                if repetitions>=max_reuse and domain!="wiki":break
                # Avoid a final addition only when it would worsen the target error.
                n=row["supervised_tokens"]
                if counts[domain]>0 and abs(counts[domain]+n-target)>abs(counts[domain]-target):break
                selections.append({**row,"repeat_index":repetitions})
                counts[domain]+=n;used[domain]+=1;idx+=1
        rng.shuffle(selections)
        all_rows[name]=selections
        actual=sum(counts.values())
        summaries[name]={"target_weights":weights,
            "actual_supervised_tokens":dict(counts),
            "actual_token_ratios":{key:counts[key]/actual if actual else 0 for key in weights},
            "target_supervised_tokens":budget,"realized_supervised_tokens":actual,
            "sample_counts":dict(used),"max_reuse":max_reuse,
            "target_error_tokens":{key:counts[key]-round(budget*v) for key,v in weights.items()}}
    output_dir.mkdir(parents=True,exist_ok=False)
    hashes={}
    for label,rows in all_rows.items():
        path=output_dir/(label+"_mixture.jsonl")
        with path.open("x",encoding="utf-8") as f:
            for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
        hashes[path.name]=digest(path)
    report={"version":"v0.13.58.23","status":"EXPERIMENT_DATA_STAGED_NOT_APPROVED",
        "seed":seed,"context_length":context,"source_manifest_sha256":digest(dataset_dir/"manifest.json"),
        "tokenizer_sha256":digest(tokenizer_path),"wiki_train_sha256":digest(wiki_path),
        "validation_sha256":digest(val_path),"replay_sources":sources,"experiments":summaries,
        "output_sha256":hashes,"sampling_basis":"supervised next-token targets (masked for replay)",
        "validation_used_for_training":False,"human_review_approved":False,
        "independent_holdout_verified":False,"training_performed":False,"production_promotion_allowed":False,
        "limitations":["Exact target ratios may be unreachable at chunk granularity or reuse cap.",
                       "Wikipedia remains unapproved and the mixtures are diagnostic only.",
                       "Validation remains a same-dump diagnostic set, not independent holdout."]}
    (output_dir/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dataset-dir",type=Path,default=Path("results/jawiki_dataset_v0135821"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--conversation",type=Path,default=Path("data/replay_conversation_approved_v013582.jsonl"))
    p.add_argument("--persona",type=Path,default=Path("data/replay_persona_approved_v013582.jsonl"))
    p.add_argument("--output-dir",type=Path,default=Path("results/jawiki_mixtures_v0135823"))
    p.add_argument("--budget",type=int,default=30000)
    p.add_argument("--context",type=int,default=512)
    p.add_argument("--seed",type=int,default=135823)
    p.add_argument("--max-reuse",type=int,default=8)
    a=p.parse_args()
    report=build(a.dataset_dir,a.tokenizer,a.conversation,a.persona,a.output_dir,a.budget,a.context,a.seed,a.max_reuse)
    print(json.dumps({"status":report["status"],"experiments":report["experiments"]},ensure_ascii=False))
    print("manifest:",a.output_dir/"manifest.json")
if __name__=="__main__":main()
