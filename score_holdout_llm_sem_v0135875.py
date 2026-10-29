#!/usr/bin/env python3
"""Score holdout questions against candidate questions using real LLM_SEM vectors.

Requires local ../LLM_SEM model and tokenizer. Never reads gold labels for scoring.
"""
import argparse
import csv
import importlib
import math
import sys
from pathlib import Path

def input_pairs(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows=list(csv.DictReader(f))
    if not rows:
        raise ValueError("empty reviewed pairs input")
    required={"query_id","query","candidate_id","candidate_question"}
    if not required.issubset(rows[0]):
        raise ValueError("missing columns "+str(required-set(rows[0])))
    queries, candidates, keys={}, {}, set()
    for row in rows:
        q,c=row["query_id"],row["candidate_id"]
        if not q or not c or not row["query"].strip() or not row["candidate_question"].strip():
            raise ValueError("empty query or candidate")
        if (q,c) in keys:
            raise ValueError("duplicate pair")
        keys.add((q,c))
        for store,k,t in ((queries,q,"query"),(candidates,c,"candidate_question")):
            if k in store and store[k]!=row[t]:
                raise ValueError("inconsistent text for "+k)
            store[k]=row[t]
    return rows,queries,candidates

def cosine(a,b):
    if len(a)!=len(b) or not a:
        raise ValueError("vector dimension mismatch")
    numer=sum(float(x)*float(y) for x,y in zip(a,b))
    a2=sum(float(x)*float(x) for x in a)
    b2=sum(float(x)*float(x) for x in b)
    if not all(math.isfinite(v) for v in (numer,a2,b2)) or a2<=0 or b2<=0:
        raise ValueError("invalid or zero semantic vector")
    return numer/math.sqrt(a2*b2)

def generate(rows, queries, candidates, encode):
    qvec={k:encode(v) for k,v in queries.items()}
    cvec={k:encode(v) for k,v in candidates.items()}
    return [{"query_id":r["query_id"],"candidate_id":r["candidate_id"],
             "score":format(cosine(qvec[r["query_id"]],cvec[r["candidate_id"]]),".12g")}
            for r in rows]

def load_encoder(root, checkpoint, tokenizer_path, device, pooling, alpha):
    root=Path(root).resolve()
    for name in ("model.py","semantic.py","tokenizer.py"):
        if not (root/name).is_file():
            raise FileNotFoundError(root/name)
    # Prevent silently importing an unrelated sibling model/tokenizer module.
    for name in ("model","semantic","tokenizer"):
        if name in sys.modules:
            raise RuntimeError("module collision: "+name)
    sys.path.insert(0,str(root))
    try:
        import torch
        lm=importlib.import_module("model").LanguageModel
        tok=importlib.import_module("tokenizer").Tokenizer
        encode_text=importlib.import_module("semantic").encode_text
        target=torch.device(device)
        model,_=lm.load_checkpoint(str(checkpoint),device=target)
        model.eval()
        tokenizer=tok.load(str(tokenizer_path))
    except Exception:
        sys.path.remove(str(root))
        raise
    def encode(text):
        result=encode_text(model,tokenizer,text,pooling=pooling,hybrid_alpha=alpha)
        return result.vector
    return encode

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--review",required=True)
    p.add_argument("--sem-root",default="../LLM_SEM")
    p.add_argument("--checkpoint",required=True)
    p.add_argument("--tokenizer",required=True)
    p.add_argument("--device",default="cuda")
    p.add_argument("--pooling",choices=["mean","last","bos","max","attention","hybrid"],default="hybrid")
    p.add_argument("--alpha",type=float,default=0.35)
    p.add_argument("--output",default="results/llm_sem_scores_v0135875.csv")
    args=p.parse_args()
    if not 0<=args.alpha<=1: p.error("alpha must be within [0,1]")
    rows,queries,candidates=input_pairs(args.review)
    encoder=load_encoder(args.sem_root,args.checkpoint,args.tokenizer,args.device,args.pooling,args.alpha)
    scores=generate(rows,queries,candidates,encoder)
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=["query_id","candidate_id","score"])
        w.writeheader();w.writerows(scores)
    print(f"LLM_SEM_REAL_VECTOR_SCORES pairs={len(scores)} queries={len(queries)} candidates={len(candidates)} output={target}")

if __name__=="__main__":
    main()
