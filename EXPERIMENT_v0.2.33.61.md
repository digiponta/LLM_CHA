# LLM_CHA v0.2.33.61 — Multi-Proposition Evidence Composition & Contradiction Detection

A deterministic, isolated experimental validator combines **two or more supported positive inclusion propositions**. The `includes` relation is only treated as transitive when explicitly authorized by `transitive_relations={"includes"}`. It never assumes that an arbitrary predicate is transitive.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.61
git pull origin v0.2.33.61
python -m py_compile multi_proposition_evidence_v023361.py
python -m unittest -v test_multi_proposition_evidence_v023361.py test_structural_evidence_integration_v023360.py
python multi_proposition_evidence_v023361.py
```

Expected **11/11 PASS**. Output: `results/multi_proposition_evidence_v023361.json` (refuses overwrite). Cases: authorized chain, not authorized, missing link, unverified/negated/reversed link, conditional mismatch and match, explicit direct counterevidence, missing source, and unsupported candidate predicate.

## Safety / boundaries

- Every used premise must have `truth=TRUE`, a nonempty source and a unique evidence identifier; the result stores the **ordered evidence ID path**, not a generated explanation.
- Explicit direct negative counterevidence blocks the requested positive conclusion. However, **general contradiction detection beyond the target pair is not yet implemented**.
- Conditions must match exactly; mixed conditions do not prove an unconditional conclusion.
- This is a restricted parser and a proof-chain fixture, **not** a general entailment model or external validation of truth.
- The experiment **does not alter `chat.py`, production Semantic Memory, checkpoint files, or `/sleep`**. The next phase would integrate candidate proof chains with the opt-in safe bridge after independent validity checks.
