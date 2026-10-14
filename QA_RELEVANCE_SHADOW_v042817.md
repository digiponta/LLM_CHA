# LLM_CHA v0.4.28.17 — Question–Answer Relevance Shadow Gate (Offline)

The v0.4.28.17 Shadow Gate is an **offline comparison against explicit human reviewer labels**, not an independently trained or automatic QA relevance predictor. It never modifies `chat.py` or Truth Gate decisions. A `false` human `final_relevant` label paired with an observed `ACCEPT` is a reviewed irrelevant accept; a `true` label paired with an `ACCEPT` is a reviewed relevant accept. Unreviewed rows stay `UNDETERMINED`. The command also exposes a review bucket for non-ACCEPT decisions where final relevance is labeled true, but this does not prove a false rejection (a relevant response can still be rejected for other valid reasons).

When the existing CSV is blank, zero cases are reviewed, and no error rate or calibration statistic is claimed. The four examples A04/A05/C05/C07 require explicit entry in `results/semantic_relevance_review_v042813.csv`; prior textual assessments are not automatically inserted into user data. Rebuild the comparison file after labeling, if desired, and provide a distinct output filename to preserve old runs.

## Windows PowerShell

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0

python -m py_compile shadow_qa_relevance_v042817.py
python -m unittest -v `
  test_shadow_qa_relevance_v042817.py `
  test_inspect_generation_gate_v042816.py `
  test_prepare_gate_review_queue_v042815.py `
  test_compare_gate_relevance_v042814.py `
  test_review_semantic_relevance_v042813.py `
  test_validate_semantic_probes_v042812.py `
  test_analyze_generation_gate_v042811.py `
  test_isolated_stage_trace_v042810.py `
  test_runtime_stage_observability_v04289.py `
  test_diagnose_pipeline_attribution_v04288.py `
  test_diagnose_false_accept_v04287.py `
  test_eval_quality_v04286.py `
  test_capture_chat_benchmark_v04283.py `
  test_prepare_chat_benchmark_v04282.py `
  test_persona_response_shadow_v0421.py

python shadow_qa_relevance_v042817.py `
  --validation results/semantic_probe_validation_v042812.json `
  --comparison results/gate_relevance_comparison_v042814.json `
  --reviews results/semantic_relevance_review_v042813.csv `
  --output results/qa_relevance_shadow_v042817.json
```

Expected 86 tests: 81 existing and five new. Unit results require Windows verification. The command does not use a GPU. The input CSV must preserve fixed fields, and sources are hashed. It will not overwrite a prior report.

Future experiments: collect explicit balanced human labels (both relevant and irrelevant), then compare a truly independent QA relevance classifier in shadow mode. Any proposed live-gate modification needs separate regressions and authorization. Development prompts are not independent holdout data.

No modifications to `main`, Truth Gate thresholds, Semantic Memory, model weights, `/sleep`, `/train` or `chat.py`.
