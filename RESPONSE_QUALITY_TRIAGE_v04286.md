# LLM_CHA v0.4.28.6 — Response Quality Evaluation (Triage)

Read-only automated triage of previously captured benchmark runs. No GPU, model inference, learning, /sleep, Truth Gate, or Semantic Memory writes.

`eval_quality_v04286.py` measures response capture, abstention (`未学習です`), replacement characters in extracted answers, recorded gate resolution and per-category case counts. Each turn includes **unscored** fields for human annotation: relevance, Japanese fluency, persona consistency, grounding, gate appropriateness and notes. It does **not** claim automatic correctness or quality measurement. A gate value of `NOT_RECORDED` means the capture lacks that detail, not that runtime skipped the gate.

Run:

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_eval_quality_v04286.py test_capture_chat_benchmark_v04283.py test_prepare_chat_benchmark_v04282.py test_persona_response_shadow_v0421.py
python eval_quality_v04286.py --input results/chat_benchmark_capture_v04284.json --output results/chat_quality_triage_v04286.json
```

Use v04284 capture for the existing complete 64-input run; it predates the diagnostic separation fix and may mark two process-normal cases as capture failures. The triage reports captured answers separately from process status. A future v04285 capture can be evaluated similarly, using a **new output filename**.

Manual labeling should distinguish factual correctness from appropriate abstention; a low agreement or shadow warning is not proof of an incorrect answer. Dev benchmark ≠ independent holdout. Do not train on the benchmark or commit captured conversations without inspecting privacy.
