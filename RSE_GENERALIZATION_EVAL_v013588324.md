# LLM_CHA v0.13.58.83.24 — Theme RSE Development Regression and Generalization Probes

This release tests the experimentally enabled `rse_live_route_v013588323` function **without** running `chat.py`, changing model weights, or touching the user's live candidate lifecycle store. All candidate stores are temporary.

12 cases: known invitation, 2 invitation paraphrases, current-activity and paraphrase abstention, factual and unrelated routing (not intercepted), pending and revoked candidate, duplicate approved candidates (review required), missing store, corrupted store. The evaluator reports an explicit pass matrix, positive coverage, and false adoption count for negative cases.

A code improvement distinguishes ambiguous **multiple approved matches** from no-match: ambiguous responses return `RSE_REVIEW_REQUIRED_EXPERIMENTAL` and 「未学習です」.

### PowerShell
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.24-rse-generalization-eval
python -m unittest -v test_rse_generalization_v013588324.py test_rse_live_route_v013588323.py test_rse_candidate_lifecycle_v013588322.py
python evaluate_rse_generalization_v013588324.py
```
Report: `results/rse_generalization_eval_v013588324.json`.

**Important limitations:** These are code-designed development fixtures with expected results chosen by the implementation author, NOT a human-reviewed independent holdout and NOT observed `chat.py` results. Passing them does not establish generalization to unscripted dialogue. The live behavior remains opt-in via `python chat.py --rse-live-experiment`; default `chat.py` is unchanged. The current test suite also does not execute Torch/model loading. Next step: independent paraphrase holdout with sealed human labels and live replay comparing enabled/disabled modes, plus broader grammar and semantic relation assessment.
