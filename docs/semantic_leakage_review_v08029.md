# LLM_CHA v0.8.0.29 — Semantic vector triage (adapter boundary)

New read-only tool: `semantic_leakage_review_v08029.py`.

Run:
```powershell
git fetch origin
git switch v0.8.0.29
git pull --ff-only origin v0.8.0.29
python -m unittest -v test_semantic_leakage_review_v08029.py
python semantic_leakage_review_v08029.py data/holdout_review_candidates_v08026.json
```
Without vector exports, the tool returns VECTORS_NOT_PROVIDED and preserves REVIEW_REQUIRED.
Do **not** invent vectors or pretend that LLM_SEM integration is connected.

To supply REAL LLM_SEM exports, create an external JSON with:
```json
{
  "embedding_space": {
    "model_id": "same-model-for-both-corpora",
    "checkpoint_sha256": "64-character-hex-digest",
    "tokenizer_sha256": "64-character-hex-digest",
    "pooling": "documented-pooling",
    "normalization": "documented-normalization",
    "dimension": 64
  },
  "vectors": [
    {"kind": "training", "id": "actual-training-id", "values": [0.1]},
    {"kind": "holdout", "id": "actual-holdout-id", "values": [0.2]}
  ]
}
```
The example values **illustrate schema only**; real arrays must have exactly
`dimension` finite components and cover every candidate ID exactly once.
Vectors MUST come from the same frozen checkpoint and tokenization/pooling pipeline.
Use a separately calibrated threshold, then:
`python semantic_leakage_review_v08029.py data/holdout_review_candidates_v08026.json --vectors path/to/export.json --threshold 0.8`

WARNING: checkpoint/tokenizer hashes are declared, not cryptographically
verified against local model files. This tool cannot establish semantic
independence, threshold calibration, or exclusion from pretraining exposure.
No automatic approvals or dataset writes.
