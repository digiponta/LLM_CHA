# LLM_CHA v0.4.28.40 — Human-Reviewed QA Dataset Workflow

Separate **human review** from the prior rule-based quality gate. The v0.4.28.39 quality JSON had 26 examples: 14 HOLD, 12 REJECT, zero approved. None of these are gold labels. This release adds an explicit, manual adjudication workflow that does NOT claim to add model training data automatically.

## Local Windows procedure

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile review_japanese_foundation_qa_v042840.py
python -m unittest -v test_review_japanese_foundation_qa_v042840.py test_gate_japanese_foundation_qa_v042839.py

python review_japanese_foundation_qa_v042840.py `
  --quality results/japanese_foundation_qa_quality_v042839.json `
  --make-template results/japanese_foundation_review_template_v042840.json
```

Edit that template in a text editor. For each HOLD candidate, compare its proposed question with the **original source answer**; fill `verified_question` (a corrected, natural, evidence-supported question), `reviewer`, `review_note`, and set `decision` from `PENDING` to `ACCEPT`, `REJECT`, or `SKIP`. REJECT cases must never be marked ACCEPT. Do **not** alter `id`, `answer`, `source`, or `gate_status`. A reviewer must actually inspect the data; filling these fields automatically is prohibited.

```powershell
python review_japanese_foundation_qa_v042840.py `
  --quality results/japanese_foundation_qa_quality_v042839.json `
  --review results/japanese_foundation_review_template_v042840.json `
  --output results/japanese_foundation_reviewed_v042840.json
```

The reviewed export contains **human-approved positive candidates only**. It deliberately retains `train_ready: false`: independently verified negatives/hard negatives, subject-group isolation, privacy/license checks and unbiased evaluation are still missing. Nothing is ingested into the model in v0.4.28.40. New output paths must not already exist (no overwrite). Previous JSONs and source dataset remain unchanged.

Tests: 8 new + 8 prior = **16** expected. Actual Windows execution pending; no claims of passed local tests. No changes to production Truth Gate, model weights, Semantic Memory, /sleep, /train, chat.py or main branch.
