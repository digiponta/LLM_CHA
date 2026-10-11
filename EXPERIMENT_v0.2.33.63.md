# LLM_CHA v0.2.33.63 — Multi-Layer Semantic Evidence Retrieval (Audit Phase)

This branch implements a **read-only, conservative four-layer audit** of atomic propositions, Subject Index, Typed Index and Unified Semantic Memory. Derived layers are **not** treated as independent verification, and matching the unified concept does not imply its `assistant` text is an independently verified proof.

- `/refaudit` is available in the existing `chat.py --session-reference-memory` mode after approving a session reference and reference-to-concept mapping.
- Deduplication key: normalized `(subject,value)` across the atomic, subject and typed layers. Duplicate derived entries do not increase evidence count.
- Atomic propositions are the canonical baseline; derived-only statements are recorded as *orphans* and never silently promoted.
- Unified Semantic Memory is concept-level; only its concept presence is audited, **not** presumed exact sentence corroboration.
- No retrieval ranking or multi-layer fact admission is implemented yet. `/refchain` remains subject to the independent reviewed evidence manifest from v0.2.33.62.

## Windows PowerShell
```powershell
git fetch origin
git switch v0.2.33.63
git pull origin v0.2.33.63
python -m py_compile chat.py multilayer_semantic_audit_v023363.py
python -m unittest -v test_multilayer_semantic_audit_v023363.py test_session_multi_evidence_bridge_v023362.py
python chat.py --session-reference-memory
```
Once `cursor` is approved and mapped: `/refaudit`.

The four audit tests exercise deduplication, concept scoping, derived-only orphans, and non-promotion of unified concept presence. All fixtures use isolated temporary paths; production Semantic Memory and LLM weights are unchanged.

## Next
An explicitly reviewed admission policy can later map this inventory into the multi-proposition proof bridge, but must not silently infer TRUE from multiple derived representations of the same atomic record.
