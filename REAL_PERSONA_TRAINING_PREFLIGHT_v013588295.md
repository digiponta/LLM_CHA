# LLM_CHA v0.13.58.82.95 — RealPersonaChat Pilot Training Preflight

This branch does **not** train or promote a model. It adds a fail-closed preflight for the previously audited CP pilot: 2,286 candidate pairs from 157 train dialogues. A structural audit is not consent or proof of privacy safety. Do not reuse CP's identity/persona as Nagato; only consider general conversational response patterns.

## 1. Windows

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.95-persona-training-preflight
python -m unittest -v test_real_persona_training_preflight_v013588295.py test_real_persona_pilot_v013588293.py
# Unless you previously reviewed and exported the corpus, this is expected to BLOCK:
python preflight_real_persona_training_v013588295.py
```

## 2. Review before export

Review the actual source license and attribution requirements, inspect the selected CP dialogue samples **locally**, check privacy and quality, and keep the Nagato persona separated. The v0.93 extractor uses an opt-in `--license-reviewed --export` workflow. Do **not** claim that it automatically detects all PII or semantic overlap. The previously reviewed source license permits CC BY-SA 4.0 uses subject to its conditions; separate privacy and persona considerations still apply.

```powershell
# Only after actual licensing, sample, and persona review:
python prepare_real_persona_pilot_v013588293.py `
 --source data-src/real-persona-chat `
 --target-speaker CP `
 --max-pairs 5000 `
 --license-reviewed --export
```

This creates `data/real_persona_pilot_v013588293.jsonl`, refusing to overwrite.

Create `results/real_persona_training_review_v013588295.json` locally, containing **truthful** review decisions and the exact SHA-256 of the exported JSONL (compute with `(Get-FileHash data/real_persona_pilot_v013588293.jsonl -Algorithm SHA256).Hash.ToLower()`):

```json
{
  "license_checked": false,
  "privacy_sample_reviewed": false,
  "persona_separation_approved": false,
  "quality_sample_approved": false,
  "dataset_sha256": "REPLACE_WITH_LOCAL_SHA256"
}
```

The flags are **not** approvals by the assistant. Change to true only after completing each corresponding review. An absent review file, missing dataset, mismatched hash, output path collision or existing experiment checkpoint blocks readiness. The preflight additionally checks exact holdout overlap, duplicate records, JSONL structure and a maximum of 5,000 records.

```powershell
python preflight_real_persona_training_v013588295.py
```

Expected result before the approvals are supplied: `BLOCKED`. `READY` is a local preflight result, not a license certificate or proof of model quality.

## 3. Only once READY: isolated experiment, not a release

Keep the original model `model/model-gpu-v1.6.2-online.pt` and the v0.88 4-epoch model immutable. Do not feed test/validation dialogue splits into training. Pilot data from one speaker may be too narrow; evaluate five prior holdout prompts and independent RealPersonaChat test dialogues, as well as Semantic Memory exact/alias retrieval before considering promotion. The existing `online_train.py` duplicates manual pairs via weight 4 by default; record that setting in any eventual experiment.

**No training command is automatically issued by this branch.**
