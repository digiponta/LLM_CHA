"""v0.13.46: audit Japanese foundation corpus before training.

Read-only; no model optimization. Reject holdout overlap and tiny training data.
Aozora formatting extraction is separate and must be explicitly reviewed.
"""
import argparse,collections,hashlib,json,statistics
from pathlib import Path

def normalize(s):
    import re,unicodedata
    return re.sub(r"\s+","",unicodedata.normalize("NFKC",s))

def ngrams(s,n=8):
    s=normalize(s)
    return {s[i:i+n] for i in range(max(0,len(s)-n+1))}

def find_overlap(train,val,holdout,threshold=.8):
    datasets={"train":train,"val":val,"holdout":holdout}
    normalized={key:[normalize(s) for s in rows] for key,rows in datasets.items()}
    exact=[];near=[]
    for left,right in (("train","val"),("train","holdout"),("val","holdout")):
        for i,s in enumerate(normalized[left]):
            for j,t in enumerate(normalized[right]):
                if s==t:
                    exact.append({"a":left,"a_index":i,"b":right,"b_index":j})
                elif min(len(s),len(t))>=16:
                    a=ngrams(s);b=ngrams(t)
                    similarity=len(a&b)/max(1,len(a|b))
                    if similarity>=threshold:
                        near.append({"a":left,"a_index":i,"b":right,"b_index":j,
                                     "jaccard_8gram":round(similarity,4)})
    return exact,near

def count_tokens(lines,tokenizer):
    return [len(tokenizer.encode(s)) for s in lines]

def readlines(p):
    if not p.is_file():raise FileNotFoundError(p)
    return [s.strip() for s in p.read_text(encoding="utf-8-sig").splitlines() if s.strip()]

def audit(train,val,holdout,tokenizer,minimum_train_tokens=100000,
          minimum_val_tokens=5000,near_threshold=.8):
    exact,near=find_overlap(train,val,holdout,near_threshold)
    counts={key:count_tokens(rows,tokenizer) for key,rows in
            (("train",train),("val",val),("holdout",holdout))}
    totals={key:sum(values) for key,values in counts.items()}
    issues=[]
    if exact:issues.append("EXACT_CROSS_SPLIT_OVERLAP")
    if near:issues.append("NEAR_CROSS_SPLIT_OVERLAP_REVIEW_REQUIRED")
    if totals["train"]<minimum_train_tokens:issues.append("INSUFFICIENT_TRAIN_TOKENS")
    if totals["val"]<minimum_val_tokens:issues.append("INSUFFICIENT_VALIDATION_TOKENS")
    return {"version":"v0.13.46","status":"READY_FOR_TRAINING" if not issues else "NOT_READY",
            "issues":issues,"sentences":{k:len(v) for k,v in
            (("train",train),("val",val),("holdout",holdout))},
            "tokens":totals,
            "mean_tokens_per_sentence":{k:round(statistics.mean(v),2) if v else 0
                                        for k,v in counts.items()},
            "cross_split_exact":exact,"cross_split_near":near,
            "limitations":["8-character Jaccard checks lexical overlap, not semantic leakage.",
                           "Historical training exposure and licenses require separate human verification.",
                           "READY is only a corpus-size/overlap readiness signal, not quality certification."]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--corpus-dir",type=Path,default=Path("results/japanese_foundation_corpus_v01345"))
    p.add_argument("--heldout",type=Path,default=Path("data/japanese_foundation_heldout_v01342.txt"))
    p.add_argument("--tokenizer",type=Path,default=Path("../LLM_GPU/model/tokenizer-v0.7-bpe.json"))
    p.add_argument("--output",type=Path,default=Path("results/japanese_foundation_audit_v01346.json"))
    p.add_argument("--min-train-tokens",type=int,default=100000)
    p.add_argument("--min-val-tokens",type=int,default=5000)
    a=p.parse_args()
    if min(a.min_train_tokens,a.min_val_tokens)<1:p.error("minimum tokens must be positive")
    if a.output.exists():p.error("refusing to overwrite report")
    from tokenizer_bpe import Tokenizer
    tok=Tokenizer.load(str(a.tokenizer))
    tr=a.corpus_dir/"train.txt";va=a.corpus_dir/"val.txt"
    train,val,heldout=readlines(tr),readlines(va),readlines(a.heldout)
    result=audit(train,val,heldout,tok,a.min_train_tokens,a.min_val_tokens)
    result["inputs_sha256"]={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in
                             (tr,va,a.heldout,a.tokenizer)}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"issues":result["issues"],
                      "tokens":result["tokens"],"exact":len(result["cross_split_exact"]),
                      "near":len(result["cross_split_near"])},ensure_ascii=False))
    print("report:",a.output)
if __name__=="__main__":main()
