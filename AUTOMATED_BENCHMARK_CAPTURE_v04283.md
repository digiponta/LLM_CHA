# LLM_CHA v0.4.28.3 — Opt-in Automated Benchmark Capture

Only branch `v0.4.0`. Does not modify `chat.py`, production Truth Gate, Semantic Memory, `/sleep`, `/train`, or checkpoints.

This script validates the 64-input, 56-case v0.4.28.2 manifest, copies code/data (excluding checkpoint/model, Git metadata, results, cache and symlinks) into a temporary workspace, launches isolated `chat.py` subprocesses with explicit `--model`, `--tokenizer`, and `--no-learn`, and passes only benchmark prompts plus `/exit`. Each SINGLE runs as its own process; each three-turn MULTI is one process. Records full transcript, heuristically extracted answer/gate, and checkpoint/tokenizer/manifest SHA256. Confirms source checkpoint SHA unchanged.

**Important limits**: A process-level working copy is not a security sandbox. `chat.py` may still resolve *absolute* paths, sibling repo assets, or network services. Output may contain personal data; do not push JSON reports to public GitHub without review. The method preserves a local test copy of queues; it does NOT make a claim that the original data sources cannot be accessed. `--run` requires explicit opt-in. Response parsing is best-effort and can miss multi-line answers. This is development evaluation, NOT an independent holdout or a measured quality pass. Do not train on benchmark questions.

## Commands
```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_capture_chat_benchmark_v04283.py test_prepare_chat_benchmark_v04282.py test_persona_response_shadow_v0421.py

# Examine plan without model execution
python capture_chat_benchmark_v04283.py --manifest results/chat_benchmark_manifest_v04282.json --checkpoint model/model-gpu-v1.6.2-online.pt --tokenizer model/tokenizer-v0.7-bpe.json --output results/chat_benchmark_capture_v04283.json

# Opt-in full run, potentially several minutes; writes new report only
python capture_chat_benchmark_v04283.py --run --manifest results/chat_benchmark_manifest_v04282.json --checkpoint model/model-gpu-v1.6.2-online.pt --tokenizer model/tokenizer-v0.7-bpe.json --output results/chat_benchmark_capture_v04283.json --timeout-per-group 240
```

The report requires a new output path. `/capture`, `/learn`, `/train` and `/sleep` are not issued. If subprocess failures occur, status and transcript are retained, but the process exits nonzero. Evaluation quality must be manually annotated against relevance, persona, fluency and grounding.
