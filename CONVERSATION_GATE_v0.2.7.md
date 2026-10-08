# LLM_CHA v0.2.7 — Context-Aware Response Quality Gate

Branch: `v0.2.7`, based on `v0.2.6`. No model weights were updated.

## Changes

The optional-on-by-default `--context-quality-gate` rejects obviously vacuous responses to explicit context continuation requests (e.g. `その話、続けて` -> `そうですね`). With `--conversation-repair` (also on by default), a rejected continuation receives a short clarifying question rather than `未学習です`. This is a deterministic repair, **not an LLM-generated answer**. The gate uses the existing v0.2.6 classifier, preserving previous diagnostic semantics.

This gate applies only after generated-answer evaluation and never inside canonical, Semantic Memory, Truth-State, `/sleep` or other retrieval-first paths. Repaired text is deliberately **not** marked as a trusted accepted model answer and does not auto-enter teaching memory. An unanswered user message can still persist as transient context.

## Local verification (PowerShell)

```powershell
git fetch origin
git switch --track origin/v0.2.7
python -m unittest -v test_conversation_quality_v027.py test_conversation_diagnostics_v026.py test_conversation_context_v025.py
python chat.py --model model/model-llm-cha-multiturn-v024.pt --tokenizer ..\LLM_TRY\model\tokenizer-v0.7-bpe.json --character nagato --dialogue-history-turns 2 --temperature 0 --show-context --show-conversation-diagnostics
```

Test:
```text
最近、小説にはまっています
SFです
その話、続けて
/reset
その話、続けて
CPUとは
GPUの並列処理が速い理由を説明して
```

Run once with `--no-context-quality-gate` and once with `--context-quality-gate` for baseline comparison. The repair response uses `selected_history` to decide whether to ask for topic or a specific part. If the previous prompt contains only merged transient user text, the selected-history count can underestimate effective context; inspect `--show-context` output.

## Limits

This heuristic is narrow: it may miss other generic answers, or reject genuinely useful brief answers in rare contexts. It cannot improve the underlying model's conversational generation. Benchmark with unseen multi-turn conversations and manual rubric before declaring a stable release. Do not promote to main without running local tests and legacy Semantic Memory/Truth-State/`/sleep` regressions.
