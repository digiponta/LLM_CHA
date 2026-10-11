# v0.2.33.56 — Verified Reference-to-Concept Mapping

**Purpose:** Keep ephemeral session reference IDs distinct from canonical semantic concepts. Add an explicit, attributed, approval-gated mapping between the two; no inferred aliases and no automatic semantic writes.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.56
git pull origin v0.2.33.56
python -m py_compile chat.py verified_reference_concept_v023356.py
python -m unittest -v test_verified_reference_concept_v023356.py test_truth_aware_reference_bridge_v023355.py
python chat.py --session-reference-memory
```

## Interactive trial
```text
You> /reset
You> 昨日の実験の続きをやって
You> カーソルでお願いします
You> はい
You> /refmapped
You> /refmap propose 量子力学 => explicit-user-confirmed-mapping
[mapping pending: map-1-v1; approve explicitly via /refmap approve TOKEN]
You> /refmap approve map-1-v1
You> /refmapped
```

Use the **actual displayed token**, not the illustrative map-1-v1 above. The concept `量子力学` here is merely a test mapping example; it must not be treated as a factual relation between 'cursor' and quantum mechanics. If no verified Semantic Memory evidence exists for that concept, the bridge returns review_required even after explicit mapping approval.

The mapping store defaults to `data/reference_concept_mapping.sqlite3` and can be overridden with `--reference-mapping-db`. It is distinct from both `data/session_reference_memory.sqlite3` and all Semantic Memory files.

## Safety boundaries
- Mapping creation alone never authorizes retrieval; `/refmap approve TOKEN` is required.
- Version-CAS checks candidate ID, mapping version, context, status and expiry. Superseded IDs cannot be approved.
- The mapped bridge calls the existing SemanticKnowledgeArchitecture only after both current reference and mapping are approved and unexpired.
- `FALSE`, `UNVERIFIED`, `CONTESTED`, `OUTDATED` responses are held for review. Even a manually set TRUE is not independent proof of correctness.
- No writes to semantic propositions or /sleep; nothing is automatically trained.
- This is a **research branch**, not merged into main. Windows/GPU results remain to be measured.
