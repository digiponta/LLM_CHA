# LLM_CHA v0.2.32.6 — Semantic Memory Backend Learning Worker

This version connects DSS-reviewed Semantic Memory records to **actual PyTorch response-only fine-tuning of a separate candidate LLM checkpoint**. The worker runs synchronously when invoked; it is a *backend command*, not a continuously running daemon.

## Flow

```text
DSS -> Semantic Memory (PENDING_REVIEW)
         -> review with a concrete, correct teacher answer
         -> APPROVED / Training Queue
         -> worker: response-only SFT + legacy replay
         -> saved candidate checkpoint, job report
         -> VALIDATING (not yet INTERNALIZED)
         -> future v0.2.32.7 independent generation/retention checks
         -> future v0.2.32.8 real LLM Direct routing
```

The DSS controller acknowledgement (e.g., "学習を目的として受け付けました") is **not used as the SFT target**. Training requires an explicitly reviewed answer. Training prompt matches the v0.2.32.4 Short form.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.32.6
git pull origin v0.2.32.6
python -m unittest -v test_semantic_backend_worker_v02326.py test_staged_semantic_internalization_v02325.py

# If needed, first create records:
python staged_semantic_internalization_v02325.py

python semantic_backend_worker_v02326.py queue
python semantic_backend_worker_v02326.py review `
  --id f8bf1478520b1dcf0969 `
  --answer "LLMの基礎として、まずトークナイザー、埋め込み、Attention、学習と推論を順番に調べましょう。"
python semantic_backend_worker_v02326.py review `
  --id 63cf99d88bc2e0e898fe `
  --answer "まずLLMの構造を学び、次に小さなTransformerを実装し、学習・推論を評価しましょう。"
python semantic_backend_worker_v02326.py queue
python semantic_backend_worker_v02326.py train `
  --model model/model-llm-cha-response-quality-v0221.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json `
  --epochs 8
```

The example IDs are from the provided DSS demo; check the IDs in your own memory before running review.

Expected success:
- `model/model-llm-cha-semantic-candidate-v02326.pt`
- `results/semantic_backend_job_v02326.json`, status `AWAITING_VALIDATION`
- Reviewed memory records move `MEMORIZED -> TRAINING -> VALIDATING`.

Existing base checkpoint is **never overwritten**, and an existing candidate output or job report cannot be overwritten. For a new experiment specify fresh `--output` and `--job-report`. Failed training marks still-TRAINING memory records as `FAILED`. To retry such records, explicitly use `transition(memory,id,"MEMORIZED")` after fixing the cause (and create fresh file paths).

## Limitations & validation

- A few manually reviewed records are only a **plumbing / learning feasibility test**. Good train NLL, successful checkpoint save, or the state `VALIDATING` does not show improved free-generation quality.
- Legacy replay contains four familiar responses, **not** an independent retention suite; response quality requires new untouched questions and topics.
- Job state persistence is file-based; **run only one worker process at a time** on a given memory file. There are no cross-process locks or crash-recovery lease checks yet. A hard process kill can leave `TRAINING` records behind. Check status and recover manually.
- This is foreground training, not a scheduler or daemon. Actual online request routing, automatic promotion, and background scheduling are **not implemented**.
- Memory can contain conversational content. Review privacy before persisting or sharing. Store model weights separately from Git unless intentionally versioning large artifacts.
