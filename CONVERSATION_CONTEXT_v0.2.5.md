# LLM_CHA v0.2.5 — Conversation Context Separation

This development branch separates transient user conversation messages from the existing trusted (accepted user/assistant pair) history.

## Behavioral contract

- Every normal user message is recorded in an in-memory transient ledger.
- A model answer rejected by the Unknown/Quality Gate is **never** added to trusted assistant history.
- When `--dialogue-history-turns N` is enabled and the query is a non-factual character conversation, immediately preceding unanswered, short user messages are folded into the current `人:` prompt. This preserves their topical text without inventing an assistant response or writing to Semantic Memory.
- Other turns follow the pre-existing Semantic Knowledge/Truth-State/`/sleep` routing and trusted history policy.
- `/reset`, training, sleep and batch resets clear both histories.
- The user text ledger is transient (not persisted or trained).

## Commands (PowerShell)

```powershell
git fetch origin
git switch --track origin/v0.2.5
python -m unittest -v test_conversation_context_v025.py test_multiturn_v024.py test_conversation_intent_v023.py test_conversation_quality_v022.py
python chat.py --model model/model-llm-cha-multiturn-v024.pt --tokenizer ..\LLM_TRY\model\tokenizer-v0.7-bpe.json --character nagato --dialogue-history-turns 2 --temperature 0
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

The expected diagnostic for a rejected `SFです` is that its text is included in the next conversational prompt, not that the LLM necessarily generates a better continuation. Compare against `--dialogue-history-turns 0`.

**Limitations:** This is an in-memory topic-carryover prototype, not an independently trained discourse representation. It concatenates unresponded utterances into a single user turn, which is only an approximation to the training distribution. The model and GPU checkpoint are unchanged. Verified retrieval paths and unknown knowledge blocking remain the independent source of truth. No GPU or local runtime regression has been executed by this GitHub change.
