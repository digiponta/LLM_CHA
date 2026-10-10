# v0.2.33.38 — Semantic Memory API Discovery Gate

The previous branch implemented a safe, file-backed **shadow** candidate store. Actual DSS and Semantic Memory callable APIs remain **unverified**. This version does not invent a connection; it introduces a read-only AST inventory and review gate for the user's local checkout, where the full implementation is available.

## PowerShell

```powershell
git fetch origin
git switch v0.2.33.38
git pull origin v0.2.33.38
python -m py_compile semantic_api_discovery_v023338.py
python -m unittest -v test_semantic_api_discovery_v023338.py test_semantic_candidate_adapter_v023337.py
python semantic_api_discovery_v023338.py --root .
```

Output: `results/semantic_api_discovery_v023338.json`. Paste/upload this report. It includes source paths, declaration lines, argument names, and potential API groupings. **It does not execute or import target modules or mutate any candidate memory.** An API name alone does not establish safety, provenance, or candidate lifecycle semantics.

## Gates before live integration

1. Confirm source module and exact interfaces for DSS assessment and semantic candidate lifecycle.
2. Confirm approved versus pending records, conversation scope and stale-reference invalidation.
3. Implement a thin adapter in a new experiment branch, isolated from stable stores, with consent, schema validation and regression tests.
4. Verify restart/rejection/expiration, then consider staged integration. Never modify LLM checkpoints or call `/sleep` during interface discovery.

This branch does **not** implement Script-Conditioned Cursor, EOS Calibration, nor any live DSS/Semantic Memory integration. Those remain separate tracks.
