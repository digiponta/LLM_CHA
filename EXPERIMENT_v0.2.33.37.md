# LLM_CHA v0.2.33.37 — Semantic Candidate Shadow Integration

The v0.2.33.36 mock candidate contract is now backed by an **atomic-written JSON shadow store**, with session-scoped records, explicit approval, provenance, expiry, rejection, invalidation and replacement of approved values. This is an *experimental interface conformance test*, **not a connection to the live Semantic Memory**.

The live DSS/Memory API was not verified via accessible repository search; assuming interfaces would risk changing stable data. Real adapters will be implemented only after examining their exact callable contracts. Unknown copy token IDs remain a separate model-generalization task.

## Steps (PowerShell)

```powershell
git fetch origin
git switch v0.2.33.37
git pull origin v0.2.33.37
python -m py_compile semantic_candidate_adapter_v023337.py
python -m unittest -v test_semantic_candidate_adapter_v023337.py test_dss_unknown_adapter_v023336.py
python semantic_candidate_adapter_v023337.py --demo
```

Two new outputs: `results/semantic_candidate_adapter_v023337.json` and `results/unknown_candidate_shadow_v023337.json`. A repeat demo refuses to overwrite existing results.

## Acceptance

Pending candidate never returned by lookup. Approved candidate is returned after recreating the store. Different context cannot read it. Expired approved records are not returned; outdated facts can be invalidated. Explicit approved replacement supersedes prior approval. Expired pending candidates cannot be approved.

## Boundaries and next work

This shadow store has **no multi-process transaction locking**. Concurrent writers might race despite atomic file replacement. Use a transactional database before concurrent or production use. TTL is wall-clock-based and attached to candidates; it is not sufficient alone to verify the meaning of relative references such as 'yesterday'. Real Semantic Memory and DSS adapter binding, candidate provenance validation, and any /sleep neural internalization remain unimplemented. No stable runtime or checkpoints are modified.
