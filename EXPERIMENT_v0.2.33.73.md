# LLM_CHA v0.2.33.73 — Truth-Aware Corpus Response Gate

## Observed issue

On the user's RTX 3070 Ti, `量子力学とは` (RAW_CORPUS_ONLY/UNVERIFIED) was blocked, while `宇宙とは` returned corpus text via `retrieval-first=HIT` even though it also reported `truth_state=UNVERIFIED`. The existing `truth_allows_direct_retrieval` policy admitted UNVERIFIED hits.

## Change

The direct CORPUS_MEMORY retrieval branch in `chat.py` now calls `corpus_answer_decision`. For a hit:

- TRUE: direct retrieval allowed, though the truth record still needs its own independent verification procedures.
- UNVERIFIED or CONTESTED: fail closed with `[truth-aware-corpus=BLOCK]` plus `未学習です`, and do not append the unverified corpus statement to the AI reply.
- FALSE or OUTDATED: bypass direct corpus retrieval and defer to existing correction/Truth-Aware downstream logic.
- No hit: no direct answer.

This is a **narrow gate** for the direct retrieval-first corpus response path. It is not evidence that all other answer paths are truth-safe. Conditional retrieval, knowledge dispatch and generated responses require separate integration tests.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.73
git pull origin v0.2.33.73
python -m py_compile chat.py truth_aware_corpus_gate_v023373.py
python -m unittest -v test_truth_aware_corpus_gate_v023373.py test_e2e_policy_benchmark_v023372.py
python chat.py --session-reference-memory
```

Expected manual sample:
```text
You> 宇宙とは
[truth-aware-corpus=BLOCK, concept='宇宙', truth_state=UNVERIFIED, ...]
AI> 未学習です
```

Then try `量子力学とは`, `時間とは` and `こんにちは` as regression observations. Do not run `/truthset` merely to force test success or silently elevate truth. Tests are authored, **not yet run** on the user's Windows machine.
