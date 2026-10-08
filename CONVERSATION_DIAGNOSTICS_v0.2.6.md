# LLM_CHA v0.2.6 — Prompt Inspection / Context Diagnostics

Branch `v0.2.6` (based on `v0.2.5`). No checkpoint modifications or training performed.

## Added

- `--show-context` prints the **exact text prompt** supplied to the model, including retained user context and accepted assistant turns. This may print user-private text; use only in trusted terminals.
- `--show-conversation-diagnostics` prints a heuristic diagnostic of boilerplate/generic replies, especially `その話、続けて → そうですね`. This mode is **observational** and does not alter accept/reject classification.
- Regression tests for diagnostic classification.

## Run

```powershell
git fetch origin
git switch --track origin/v0.2.6
python -m unittest -v test_conversation_diagnostics_v026.py test_conversation_context_v025.py test_conversation_intent_v023.py test_conversation_quality_v022.py
python chat.py --model model/model-llm-cha-multiturn-v024.pt --tokenizer ..\LLM_TRY\model\tokenizer-v0.7-bpe.json --character nagato --dialogue-history-turns 2 --temperature 0 --show-context --show-conversation-diagnostics
```

Conversation:
```text
最近、小説にはまっています
SFです
その話、続けて
/reset
その話、続けて
CPUとは
GPUの並列処理が速い理由を説明して
```

Compare the same checkpoint with `--dialogue-history-turns 0`. To isolate effects of checkpoint differences, repeat with `model/model-llm-cha-rpc-replay-v021.pt`; hold decoding settings fixed.

## Interpretation

The `context_turns` diagnostic counts accepted chat pairs, *not* rejected user-only context. The `transient_context` debug field indicates whether pending user input has been folded into the prompt. The full printed prompt is the definitive check.

A high sem_agreement does **not** prove response relevance or a continuation. Distinguish (1) prompt transport, (2) generation quality, (3) answer-gate accuracy, and (4) canonical-knowledge routing.

Because v0.2.6 is diagnostic-only, no quality improvement is claimed. Human scoring on unseen conversations and checks for no incorrect knowledge-route changes remain prerequisites for release.
