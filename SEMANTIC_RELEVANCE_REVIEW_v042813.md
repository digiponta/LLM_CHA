# LLM_CHA v0.4.28.13 — Semantic Agreement vs. Answer Relevance (Human Review)

Branch: `v0.4.0`. Adds `review_semantic_relevance_v042813.py` and five regression tests. This is a **read-only, human-in-the-loop** review workflow based on the prior `semantic_probe_validation_v042812.json` (64 turns). It does not equate lexical probe identity, Gate scores, or confidence with relevance or correctness.

The first command exports 64 rows to a CSV editable in Excel or a text editor. Annotators may fill `primary_relevant`, `probes_semantically_equivalent`, `final_relevant`, and `gate_appropriate` using exactly `true`, `false`, or blank. **Do not change** immutable source columns (`id`, `turn`, `question`, `final_answer`, `gate_resolution`, `candidate_alignment`, `literal_probe_identity`). Blank means *not evaluated*, not false. `notes` is unrestricted. The import validates the immutable source columns, labels, duplicates, and row IDs, then reports only explicitly human-labeled ACCEPT / relevance conflicts. It never invents quality percentages or root-cause attribution.

## Windows commands

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0

python -m unittest -v `
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

python review_semantic_relevance_v042813.py `
  --analysis results/semantic_probe_validation_v042812.json `
  --export-template results/semantic_relevance_review_v042813.csv

# AFTER filling the CSV:
python review_semantic_relevance_v042813.py `
  --analysis results/semantic_probe_validation_v042812.json `
  --reviews results/semantic_relevance_review_v042813.csv `
  --output results/semantic_relevance_review_summary_v042813.json
```

Expected test count: **66** (61 prior + 5 new; verify on user's Windows host). The output is new-only, and SHA-256 hashes bind it to the inputs. The source benchmark is development-only. Actual pre-Gate candidate text is present in `generation_gate_analysis_v042811.json` and `semantic_probe_validation_v042812.json`, but the CSV contains final answers and labels only; manually consult candidate text before labeling `probes_semantically_equivalent` and `primary_relevant`. In multi-turn cases where candidate attribution is unresolved, leave those fields blank.

No model/Truth Gate threshold changes, no learning, no /sleep, and no modifications to chat.py or Semantic Memory.
