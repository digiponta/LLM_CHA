# LLM_CHA v0.2.9 — Dialogue State Tracking & Repetition Reduction

Development branch `v0.2.9` based on `v0.2.8`. Model weights and semantic databases are unchanged.

## Implemented

- `dialogue_state_v029.py`: detect whether a short user utterance is likely to answer the immediately preceding assistant question.
- `repeat_check`: normalized string similarity of newly generated assistant output versus the last accepted assistant output. If the user just answered the assistant's question and proposed reply nearly repeats it, reject as `GATE_REVIEW` instead of `KNOWN`.
- `--show-dialogue-state`: inspect state and similarity for each generated reply.
- `--no-dialogue-repetition-gate`: disable for A/B regression. Default gate enabled.
- Only the generated conversational route is affected; factual retrieval and internalized verifier remain outside scope.

## Local validation

```powershell
git fetch origin
git switch --track origin/v0.2.9
python -m unittest -v test_dialogue_state_v029.py test_conversation_quality_v027.py test_conversation_context_v025.py
python chat.py --model model/model-llm-cha-quality-v028.pt --tokenizer ..\LLM_TRY\model\tokenizer-v0.7-bpe.json --character nagato --dialogue-history-turns 2 --temperature 0 --show-context --show-dialogue-state --show-conversation-diagnostics
```

Test sequence: `最近、小説にはまっています` → `SFです` → `その話、続けて` → `/reset` → `CPUとは`.

## What is not done

- **Candidate reranking** and **Dialogue-Aware SFT** are future follow-ons, not silently claimed as implemented.
- Rejected repeated questions fall back to the current unknown response; this does not automatically generate a new substantive answer. A future version should evaluate alternative candidate replies against both dialogue state and the existing semantic gate before selection.
- Similarity threshold 0.76 and 35-character short-turn rule are provisional heuristics, not calibrated against a large held-out benchmark.
- Runtime unit tests and GPU evaluations have not been executed through this GitHub update; the user's local environment must validate before merging into main.
