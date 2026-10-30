# v0.13.58.82.29 — Single-turn conditioned prompt fix

A user log exposed a critical framing bug: the four-line evidence prompt was interpreted by chat.py as four separate questions ("次の引用資料...", "話題...", "資料...", "回答..."). This produced multiple unrelated AI> answers, polluted the knowledge/gate-review queues, and misaligned the GUI's one-request/one-response FIFO.

The conditioned prompt is now normalized to one newline-free line and truncated to a bounded excerpt before sending through the interactive CLI. The GUI refuses any accidental multiline prompt and registers pending inference before writing to the subprocess. Unknown or unsupported candidates still fall back to attributed reference text. The local Transformer may continue to reject unfamiliar instructions; this release fixes transport framing, **not** LLM instruction-following or factual accuracy.

## PowerShell validation

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.29-single-turn-conditioned
python -m unittest -v test_single_turn_conditioned_v013588229.py test_evidence_conditioned_generation_v013588228.py
python chat_gui.py
```

Test: `宇宙とは` -> `CPU` -> `宇宙の話に戻って` -> `もう少し詳しく`. In the diagnostics expect exactly one `You>` / `AI>` exchange for `[Evidence-Conditioned LLM] 宇宙膨張`, not separate `You>` inputs for the prompt's labels. Check `[Evidence Gate]` and sourced fallback.

Note: external Wikipedia content remains unverified; no auto-training or promotion.
