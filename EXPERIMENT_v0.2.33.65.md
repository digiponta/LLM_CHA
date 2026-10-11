# LLM_CHA v0.2.33.65 — Raw Corpus → Semantic Proposition Candidate Lifecycle

This version introduces a **separate, isolated SQLite candidate store**. The system only extracts complete sentences matching a restricted, deterministic grammar and the explicitly approved reference-to-concept mapping. All extracted candidates begin as `PENDING`. `APPROVED` is a human *review decision*, **not** a `TRUE` Truth State and not permission to make unsupported factual assertions.

## Scope

- New `proposition_candidate_lifecycle_v023365.py` with extraction, SHA-256 source digest and stable candidate IDs, scope-isolated listing, and one-way pending→approved/rejected transitions.
- New opt-in `chat.py` commands `/refcandidate propose STATEMENT`, `/refcandidates`, `/refcandidate approve TOKEN`, `/refcandidate reject TOKEN`.
- Each requires the existing approved session reference and approved concept mapping; the candidate must have a subject equal to that mapped concept.
- No automatic ingestion into Atomic, Subject, Typed, Unified, or Truth State stores. No model updates or `/sleep`.
- This phase uses **user-submitted explicit source text**, *not automatic bulk extraction from data-nagato.txt*. Source linkage is recorded as `user-submitted-explicit-text`; external provenance checks remain future work.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.65
git pull origin v0.2.33.65
python -m py_compile chat.py proposition_candidate_lifecycle_v023365.py
python -m unittest -v test_proposition_candidate_lifecycle_v023365.py test_semantic_coverage_admission_v023364.py
python chat.py --session-reference-memory
```

After approving `cursor` and mapping it to `量子力学`:

```text
/refcandidate propose 量子力学は物理学の分野である。
/refcandidates
/refcandidate approve candidate-...
/refcandidates
/refcoverage
```

The example is a *review candidate*, not a verified factual record. Normal `/refcoverage` and `/refchain` remain fail-closed unless their own evidence requirements are met.

## Next

Add read-only, source-anchored extraction from the original corpus using stable text offsets and source checksums, before considering an explicit admission policy. Importantly, corpus text and human approval alone are not proof of factual correctness.
