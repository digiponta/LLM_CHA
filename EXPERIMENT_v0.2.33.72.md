# LLM_CHA v0.2.33.72 — Integration Policy Benchmark (Offline Observation)

This release starts the **end-to-end evaluation** program recommended by the research assessment, rather than adding another lexical classifier rule. It defines 11 **policy checkpoints** across session reference management, evidence gating, and persona isolation.

Important: This is an **observation/annotation harness**, not an automated `chat.py` runner or LLM accuracy benchmark. Until actual observations from the user's runtime are recorded, its results are `policy_metrics: null`. A passing unit-test suite verifies scorer behavior, **not** integration success.

## PowerShell

```powershell
git fetch origin
git switch v0.2.33.72
git pull origin v0.2.33.72
python -m py_compile e2e_policy_benchmark_v023372.py
python -m unittest -v test_e2e_policy_benchmark_v023372.py test_epistemic_stabilization_v023371.py
python e2e_policy_benchmark_v023372.py
Copy-Item results/cha_e2e_observations_v023372.json results/cha_e2e_review_v023372.json
python chat.py --session-reference-memory
```

The benchmark template `results/cha_e2e_observations_v023372.json` contains eleven `UNRUN` checkpoints: reference clarification/confirmation/commit/status, evidence BLOCK/discovery behavior, and persona controls. These are **stateful scenarios**; run them in valid order and with the mapping and corpus prerequisites set up before evidence cases. Commands (particularly persona IDs and `/truth`) should be checked in the active runtime help; if command syntax differs, record a mismatch rather than silently changing the fixture. Record each actual `observed` policy label plus nonempty `run_id`, `evidence` excerpt, `review_status: "OBSERVED"`. Do not mark a scenario observed without running it.

```powershell
python e2e_policy_benchmark_v023372.py --score results/cha_e2e_review_v023372.json
```

Metrics are **policy checkpoint agreement on observed cases**, not response factual accuracy, reference resolution quality, model generalization, or safety certification. Partial observations report their own denominator; absence of evidence is never scored as success. Factual correctness and positive admission require a separate independently grounded test suite.

No changes to `chat.py`, Truth State, Semantic Memory, stored corpus candidates or model weights.
