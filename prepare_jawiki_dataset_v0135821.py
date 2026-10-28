"""v0.13.58.21: article-grouped Wikipedia dataset staging (no training).

Source must match clean_candidates SHA in v0.13.58.19 quality report.
Validation is a diagnostic same-dump split, NOT an independent holdout.
Chunk token IDs directly; preserve source/article/paragraph provenance.
"""
import argparse,hashlib,json,random,collections
from pathlib import Path

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def prepare(source,quality_report,tokenizer_path,output_dir,val_fraction=.1,seed=135821,max_tokens=512):
    if output_dir.exists():raise FileExistsError(output_dir)
    if not 0<val_fraction<1:raise ValueError("invalid val_fraction")
    if not 2<=max_tokens<=512:raise ValueError("max_tokens outside 2..512")
    q=json.loads(quality_report.read_text(encoding="utf-8-sig"))
    if digest(source)!=q.get("sha256",{}).get("clean_candidates.jsonl"):
        raise ValueError("source SHA does not match cleaner report")
    from tokenizer_bpe import Tokenizer
    tok=Tokenizer.load(str(tokenizer_path))
    articles=collections.defaultdict(list)
    with source.open(encoding="utf-8-sig") as f:
        for lineno,line in enumerate(f,1):
            if not line.strip():continue
            item=json.loads(line)
            if item.get("approval")!="PENDING_REVIEW" or item.get("auto_promote") is not False:
                raise ValueError(f"unexpected approval state: {lineno}")
            aid=str(item.get("article_id",""))
            if not aid or not item.get("title") or not str(item.get("source_url","")).startswith("https://ja.wikipedia.org/"):
                raise ValueError(f"invalid provenance: {lineno}")
            if not isinstance(item.get("text"),str) or not item["text"].strip():
                raise ValueError(f"missing text: {lineno}")
            articles[aid].append(item)
    ids=sorted(articles)
    if len(ids)<2:raise ValueError("at least 2 articles required for split")
    random.Random(seed).shuffle(ids)
    nval=min(len(ids)-1,max(1,round(len(ids)*val_fraction)))
    val=set(ids[:nval])
    records={"train":[],"validation":[]}
    for aid in sorted(articles):
        partition="validation" if aid in val else "train"
        for item in articles[aid]:
            token_ids=tok.encode(item["text"],add_bos=True,add_eos=True)
            # Chunks overlap at one token, preserving next-token targets.
            for start in range(0,len(token_ids)-1,max_tokens):
                seq=token_ids[start:start+max_tokens+1]
                if len(seq)<2:continue
                records[partition].append({
                    "article_id":aid,"title":item["title"],"url":item["source_url"],
                    "paragraph_index":item.get("paragraph_index"),
                    "chunk_index":start//max_tokens,
                    "token_ids":seq,"supervised_tokens":len(seq)-1,
                    "approval":"PENDING_REVIEW","auto_promote":False})
    if not records["train"] or not records["validation"]:raise ValueError("empty split")
    if set(x["article_id"] for x in records["train"]) & set(x["article_id"] for x in records["validation"]):
        raise AssertionError("article leakage")
    output_dir.mkdir(parents=True,exist_ok=False)
    checksums={}
    for name,rows in records.items():
        path=output_dir/(name+"_chunks.jsonl")
        with path.open("x",encoding="utf-8") as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
        checksums[path.name]=digest(path)
    manifest={"version":"v0.13.58.21","status":"STAGED_NOT_APPROVED",
        "source_sha256":digest(source),"tokenizer_sha256":digest(tokenizer_path),
        "seed":seed,"val_fraction":val_fraction,"max_context_tokens":max_tokens,
        "articles":{"total":len(articles),"train":len(articles)-len(val),"validation":len(val)},
        "chunks":{k:len(v) for k,v in records.items()},
        "supervised_tokens":{k:sum(r["supervised_tokens"] for r in v) for k,v in records.items()},
        "file_sha256":checksums,"article_split_disjoint":True,
        "validation_scope":"SAME_DUMP_DIAGNOSTIC_ONLY",
        "independent_holdout_verified":False,"human_review_approved":False,
        "training_performed":False,"production_promotion_allowed":False,
        "notes":["Chunk boundaries overlap by one token to preserve shifted labels.",
                 "Historical exposure of the base checkpoint is unknown.",
                 "JSONL holds token IDs, not approved training examples.",
                 "Wikipedia source attribution and license obligations must be maintained."]}
    (output_dir/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=Path("results/jawiki_clean_v0135819/clean_candidates.jsonl"))
    p.add_argument("--quality-report",type=Path,default=Path("results/jawiki_clean_v0135819/quality_report.json"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output-dir",type=Path,default=Path("results/jawiki_dataset_v0135821"))
    p.add_argument("--validation-fraction",type=float,default=.1)
    p.add_argument("--seed",type=int,default=135821)
    p.add_argument("--max-tokens",type=int,default=512)
    a=p.parse_args()
    r=prepare(a.source,a.quality_report,a.tokenizer,a.output_dir,a.validation_fraction,a.seed,a.max_tokens)
    print(json.dumps({"status":r["status"],"articles":r["articles"],"chunks":r["chunks"],
       "supervised_tokens":r["supervised_tokens"],"independent_holdout_verified":False},ensure_ascii=False))
    print("manifest:",a.output_dir/"manifest.json")
if __name__=="__main__":main()
