# LLM_CHA v0.7.15 — Isolated Four-Fact GPU Evaluation

This release adds a **new experiment** over the four synthetic v0.7.9 facts
(blue key, red bridge, green clock and white box). Existing production
`chat.py`, trusted checkpoints, and real Approved/Candidate Memory are
unchanged.

The runner creates a **new isolated directory**, trains one experimental
adapter (rank 16, 30 epochs, LR 1e-3 by default), and measures:

1. **Four exact training-question reconstructions** using the v0.7.13
   Candidate-consistency gate.
2. **Eight held-out question paraphrases** (answer strings are present in
   training; this does not prove general factual transfer).
3. **Two absent-knowledge questions**, which must not invoke the adapter.
4. **One synthetic Approved routing probe**. It must bypass the adapter.

The synthetic Approved probe measures only *route precedence* and is not a
verified real Approved QA; therefore `approved_retention_certified=false`
even when `protected_route_preserved=true`. The experiment does not
approve or promote any actual fact.

## PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch --track origin/v0.7.15
python -m unittest -v test_multi_fact_validation_v0715.py test_multi_candidate_audit_v0714.py test_candidate_response_validation_v0713.py
python run_multi_fact_validation_v0715.py --output-dir results/multi_fact_v0715
```

If the output directory already contains experiment data, choose a NEW path:
```powershell
python run_multi_fact_validation_v0715.py --output-dir results/multi_fact_v0715_run2
```

The full report contains individual case outputs in
`results/multi_fact_v0715/summary_v0715.json`.

**Limitations:** No user-verified Protected QA data were evaluated.
A perfect route-protection result must not be confused with measured
knowledge-retention accuracy. Factual verification is NOT_PERFORMED.
The shared experimental Adapter may fail to learn all four facts and
may have interference; those are the outcomes this runner measures.
