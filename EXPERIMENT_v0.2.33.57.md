# LLM_CHA v0.2.33.57 — Evidence-Grounded Semantic Response Validation

## Goal

Add `/refevidence` to the **opt-in** chat.py reference subsystem. The query requires:

1. An approved and non-expired session reference.
2. An explicitly approved and non-expired reference-to-concept mapping.
3. A response through the existing `SemanticKnowledgeArchitecture.resolve`.
4. Truth State `TRUE`, a supported knowledge state, an allowlisted dispatcher action, a nonempty answer and **provenance metadata** with non-placeholder source and evidence/origin.

The failure path suppresses answer text, returning an explicit reason. No writes to Semantic Memory, no automatic knowledge promotion, and no `/sleep`.

**Important:** Provenance metadata and a TRUE label are necessary but **not sufficient to prove external factual correctness**. `/refevidence` produces an evidence *candidate*; this version does not perform independent document verification or pass the answer into free-form LLM generation.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.57
git pull origin v0.2.33.57
python -m py_compile chat.py evidence_grounded_reference_v023357.py
python -m unittest -v test_evidence_grounded_reference_v023357.py test_verified_reference_concept_v023356.py
python chat.py --session-reference-memory
```

Use `/reset`, select and approve `cursor` via the usual clarification flow, ensure the concept mapping has been approved with `/refmap propose ...` followed by `/refmap approve TOKEN`, then run `/refevidence`. Existing `/refmapped`, `/reftruth` and `/refknowledge` remain available.

## Constraints

- No inference of aliases or new evidence.
- No claim of verified citations from provenance's string representation.
- No promotion of raw-corpus-only content to trusted evidence.
- Existing programmatic unit tests use fixture semantics and do not replace real GPU validation.
- Not yet merged into main.
