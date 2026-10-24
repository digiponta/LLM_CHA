"""v0.8.0.29: read-only vector-space leakage triage.

Consumes externally generated LLM_SEM embeddings with explicit model identity;
does NOT generate vectors or establish semantic independence.
"""
import argparse
import json
import math
from pathlib import Path
from audit_holdout_independence_v08028 import review as lexical_review
from unapproved_llm_intake_v074446 import _read

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def cosine(a, b):
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(x*x for x in b))
    if na <= 0 or nb <= 0:
        raise ValueError("ZERO_VECTOR")
    return sum(x*y for x,y in zip(a,b))/(na*nb)

def check_vectors(payload, holdout_ids, train_ids):
    if not isinstance(payload, dict):
        raise ValueError("INVALID_VECTOR_DATA")
    meta = payload.get("embedding_space")
    if not isinstance(meta, dict):
        raise ValueError("EMBEDDING_SPACE_REQUIRED")
    for field in ("model_id", "checkpoint_sha256", "tokenizer_sha256", "pooling", "normalization"):
        if not isinstance(meta.get(field), str) or not meta[field].strip():
            raise ValueError("SPACE_METADATA_MISSING:" + field)
    if len(meta["checkpoint_sha256"]) != 64 or len(meta["tokenizer_sha256"]) != 64 or any(
        c not in "0123456789abcdefABCDEF" for name in ("checkpoint_sha256","tokenizer_sha256") for c in meta[name]):
        raise ValueError("INVALID_CHECKPOINT_OR_TOKENIZER_SHA256")
    dim = meta.get("dimension")
    if type(dim) is not int or dim <= 0:
        raise ValueError("INVALID_DIMENSION")
    rows = {}
    vectors = payload.get("vectors")
    if not isinstance(vectors, list):
        raise ValueError("VECTORS_LIST_REQUIRED")
    for r in vectors:
        if not isinstance(r, dict) or r.get("kind") not in ("training", "holdout"):
            raise ValueError("INVALID_VECTOR_RECORD")
        key = (r.get("kind"), r.get("id"))
        if not isinstance(key[1], str) or not key[1] or key in rows:
            raise ValueError("DUPLICATE_OR_INVALID_VECTOR_ID")
        v = r.get("values")
        if not isinstance(v,list) or len(v) != dim or any(
            isinstance(n,bool) or not isinstance(n,(int,float)) or not math.isfinite(n) for n in v):
            raise ValueError("INVALID_VECTOR_VALUES")
        if not any(v):
            raise ValueError("ZERO_VECTOR")
        rows[key] = v
    expected = {("training", id) for id in train_ids} | {("holdout", id) for id in holdout_ids}
    if set(rows) != expected:
        raise ValueError("VECTOR_IDS_MISMATCH")
    return rows, meta

def review(source, store, vector_path=None, threshold=None):
    baseline = lexical_review(source, store)
    if baseline["status"] not in ("REVIEW_REQUIRED", "MANUAL_REVIEW_RECORDED"):
        return baseline
    baseline["vector_analysis_status"] = "NOT_RUN"
    baseline["semantic_independence_verified"] = False
    baseline["formal_holdout_approved"] = False
    baseline["written"] = False
    if vector_path is None:
        baseline["vector_analysis_status"] = "VECTORS_NOT_PROVIDED"
        return baseline
    if threshold is None or not 0.0 < threshold <= 1.0:
        baseline["vector_analysis_status"] = "THRESHOLD_NOT_CALIBRATED"
        return baseline
    try:
        holdout = load_json(source)["records"]
        train = _read(store)["candidates"]
        h_ids = [r["id"] for r in holdout]
        t_ids = [r["id"] for r in train]
        if len(set(h_ids)) != len(h_ids) or len(set(t_ids)) != len(t_ids):
            raise ValueError("DUPLICATE_DATASET_IDS")
        payload = load_json(vector_path)
        vectors, meta = check_vectors(payload,h_ids,t_ids)
        results = []
        for id in h_ids:
            ranked = sorted(({"candidate_id":t,"cosine":round(cosine(vectors[("holdout",id)],
                                      vectors[("training",t)]),6)} for t in t_ids),
                            key=lambda x:x["cosine"],reverse=True)
            results.append({"id":id, "top_matches":ranked[:3],
                            "possible_overlap":bool(ranked and ranked[0]["cosine"] >= threshold)})
    except (OSError,ValueError,KeyError,TypeError,UnicodeError) as exc:
        baseline["vector_analysis_status"] = "INVALID_VECTOR_INPUT"
        baseline["vector_error"] = str(exc)
        return baseline
    baseline["vector_analysis_status"] = "VECTOR_SCREEN_COMPLETED"
    baseline["embedding_space"] = meta
    baseline["cosine_threshold"] = threshold
    baseline["vector_results"] = results
    baseline["calibration_verified"] = False
    # Signal suspicious matches but never clear the human review.
    if any(x["possible_overlap"] for x in results):
        baseline["status"] = "REVIEW_REQUIRED"
    return baseline

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",nargs="?",default="data/holdout_review_candidates_v08026.json")
    parser.add_argument("--store",default="data/unapproved_llm_candidates_v074446.json")
    parser.add_argument("--vectors",default=None)
    parser.add_argument("--threshold",type=float,default=None)
    a=parser.parse_args()
    print(json.dumps(review(a.source,a.store,a.vectors,a.threshold),ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
