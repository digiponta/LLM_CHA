# LLM_CHA v0.4.28.28 — Semantic QA Relevance Model Contract

This release defines a **non-operative interface**, not a trained model or demonstrated quality improvement. It prepares 64 question/final-answer pairs for future cross-encoder or NLI experiments and records previously generated ChatGPT provisional annotations **only as separate development reference labels**, never as model outputs or independent human truth.

The CLI exports a JSON contract with null `model_decision` and null `model_score`. An optional external model prediction importer validates exactly 64 cases and accepts decision `RELEVANT`, `IRRELEVANT`, or `ABSTAIN`; optional numeric score is 0–1 and uncalibrated. There is no automatic model execution, no trained weights, no accuracy estimate, and no deployment gate.

PowerShell:

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile semantic_qa_model_contract_v042828.py
python -m unittest -v test_semantic_qa_model_contract_v042828.py test_compare_qa_shadows_v042827.py

python semantic_qa_model_contract_v042828.py `
  --validation results/semantic_probe_validation_v042812.json `
  --labels results/chatgpt_qa_labels_v042823.json `
  --output results/semantic_qa_model_contract_v042828.json
```

Optional external prediction import after implementing an actual model:
```powershell
python semantic_qa_model_contract_v042828.py `
  --validation results/semantic_probe_validation_v042812.json `
  --labels results/chatgpt_qa_labels_v042823.json `
  --predictions results/external_semantic_qa_predictions.json `
  --output results/semantic_qa_validated_predictions_v042828.json
```

Prediction file schema example (fragment only; all 64 decisions required):
```json
{
  "schema":"llm_cha_semantic_qa_predictions_v1",
  "method":"cross_encoder",
  "dataset_split":"DEVELOPMENT_ONLY",
  "predictions":[{"id":"A01","turn":1,"decision":"ABSTAIN","score":null}]
}
```

The 64-case existing benchmark is DEVELOPMENT_ONLY: split labels cannot claim independent holdout. Before evaluation or threshold fitting, collect an untouched external set with new prompts and reviewed answers, and audit provisional ChatGPT labels. Expected focused unit tests: 11 (6 new and 5 existing), pending Windows verification. No changes to live Truth Gate, chat.py, model weights, Semantic Memory, /sleep or /train.
