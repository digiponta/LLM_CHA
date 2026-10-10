# LLM_CHA v0.2.33.39 — Real DSS Purpose Controller / Reference Resolution Bridge

The **real** deterministic DSS purpose controller in `purpose_confidence_v02311.py` exposes `DSS()` and `respond(dss, text) -> (state, action, reply)`. It is used directly for normal utterances, maintaining one DSS state per conversation ID.

For referential ambiguity (“昨日の実験の続きをやって”), a separate `IntegrationResolver` (v0.2.33.36) is selected. That route uses the **MockDSS** narrow reference parser and the `JsonCandidateStore` isolated shadow store (v0.2.33.37). It is **not** a real DSS-based referential ambiguity detector. This separation avoids corrupting the DSS purpose state with short replies like "cursor".

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.39
git pull origin v0.2.33.39
python -m py_compile real_dss_reference_bridge_v023339.py
python -m unittest -v test_real_dss_reference_bridge_v023339.py test_semantic_candidate_adapter_v023337.py
python real_dss_reference_bridge_v023339.py --demo
```

Outputs `results/real_dss_reference_bridge_v023339.json` and `results/reference_shadow_v023339.json`; refuses to overwrite.

## Boundaries

- The DSS purpose controller is real project code, but it is deterministic and limited to its declared topic/purpose patterns.
- The referent assessor is still the **mock rule-based** resolver.
- Approved user reference records are kept in the experimental JSON shadow store, **not** the existing staged Semantic Memory teacher records or the conditional proposition queue.
- No writes to production training memory, no LLM checkpoints, no `/sleep` learning.
- Reference-record TTL, context scoping and invalidation remain essential. Context ID `A` alone is not a durable identity for 'yesterday'; production needs time- and activity-scoped referent revisions.
- This bridge is an experimental composition; no integration into the stable `chat.py` runtime.
