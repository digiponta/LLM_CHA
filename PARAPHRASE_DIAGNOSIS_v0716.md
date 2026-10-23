# LLM_CHA v0.7.16 — Dual-LLM Paraphrase & Interference Diagnosis

The design remains **two isolated knowledge paths**:
- Trusted LLM + Approved Semantic Memory + Trusted Adapter.
- Experimental LLM + Candidate Semantic Memory + Experimental Adapter.

The user-facing router tries Trusted first. A qualifying UNKNOWN may consult
Experimental, but Experimental content remains unverified and cannot be
automatically promoted or copied as Trusted weights.

v0.7.15 successfully replayed 4/4 synthetic Candidate training questions;
8/8 paraphrase holdouts **failed exact output matching**. v0.7.16 adds
**read-only diagnosis** rather than claiming an improvement prematurely.

The diagnostics classify each of the eight holdout outputs as:
exact, cross-fact confusion, reference-containing near miss, empty, or other.
A separate GPU probe measures the first reference-answer token's rank and
probability under Base/Trusted/Experimental routes.

## Commands

```powershell
git fetch origin
git switch --track origin/v0.7.16
python -m unittest -v test_paraphrase_diagnostics_v0716.py test_multi_fact_validation_v0715.py
python diagnose_paraphrase_v0716.py --report results/multi_fact_v0715/summary_v0715.json --output results/multi_fact_v0716/diagnosis.json
python diagnose_token_rank_v0716.py --summary results/multi_fact_v0715/summary_v0715.json --checkpoint results/multi_fact_v0715/experimental-adapter.pt --output results/multi_fact_v0716/token_ranks.json
```

These scripts do not retrain, approve, or change model weights. They do not
prove factual accuracy. The next step is to use their concrete findings to
select a training/semantic retrieval fix **without contaminating the current
eight held-out paraphrases**. Any new paraphrase training data should be
drawn from a separate set with an independent holdout.
