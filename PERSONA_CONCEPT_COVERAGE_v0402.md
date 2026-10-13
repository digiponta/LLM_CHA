# LLM_CHA v0.4.2 — Persona Concept Coverage Diagnosis

Read-only comparison of **数学, 量子力学, 文学, 小説** in the raw persona corpus. This diagnoses why concepts may be known to the corpus but return `未学習です` at runtime.

`persona_concept_coverage_v0402.py` reports: raw exact-literal segment evidence (capped at 30), ranked Persona response eligibility, line/segment excerpts, and MEANS_OF candidate counts. It does **not** inspect the saved subject-index database or call the full runtime dispatcher/Truth Gate, so `runtime_truth_state` and `runtime_route` are explicitly `NOT_PROBED`. The earlier console trace already showed `文学` and `小説` as `UNKNOWN`, but this diagnostic cannot establish why without examining its report and tracing the runtime separately.

## Run

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_persona_concept_coverage_v0402.py test_persona_reviewed_retrieval_v0401.py
python persona_concept_coverage_v0402.py --corpus data/data-nagato.txt --report results/persona_concept_coverage_v0402.json
python verify_integration_v0366.py --gpu --legacy --timeout 240
```

Please share `results/persona_concept_coverage_v0402.json` and command output. Decide whether search coverage or runtime routing is at fault **from the measured evidence** before modifying the current Truth Gate. No model/checkpoint files, Persona memory, or original corpus are changed.
