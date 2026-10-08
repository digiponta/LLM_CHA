# LLM_CHA v0.2.3 — Character Intent and Context Prototype

Development branch `v0.2.3`. This is a controlled *runtime routing* experiment; it does not retrain the 8.96M parameter checkpoint.

## New behavior

When `--character nagato` is active, narrowly matched identity, gratitude, fatigue, casual invitation and book-follow-up utterances can be answered from profile metadata / limited accepted conversation history.

Example:
```text
You> お名前を伺えますか
長門有希> 長門有希。
[character-intent=identity, source=profile/context, generation=0]
```

The profile's `display_name` supplies identity, so output is not proof that the model learned the paraphrase. Factual queries (including GPU, CPU) continue through the existing Semantic Memory, Truth-State and Unknown Gate paths. Intent answers are not automatically submitted to learning queues; `last_ai_reply` is cleared to prevent accidentally approving them with `/good`. `/reset` clears the same conversation history used for book follow-ups.

Limitations: pattern-matched intents, not robust language understanding. Book follow-up is a safe conversation prompt, not a factual summary or a general multi-turn architecture. Model prompting remains unchanged and existing `context_turns=0` for the model may still occur.

## Local tests
```powershell
git fetch origin
git switch --track origin/v0.2.3
python -m unittest -v test_conversation_intent_v023.py test_conversation_quality_v022.py
python chat.py --model model/model-llm-cha-rpc-replay-v021.pt --tokenizer ..\LLM_TRY\model\tokenizer-v0.7-bpe.json --character nagato --temperature 0
```

Probe:
- お名前を伺えますか
- 自分が何者か説明して
- 今日はくたくたです
- 助かりました
- 少しおしゃべりしませんか
- 昨日は科学の本を読んだ
- その本は面白かった？
- CPUとは
- GPUの並列処理が速い理由を説明して

Run `/character off` and repeat the probes to assess compatibility. Do not merge into `main` before CPU tests and legacy semantic regressions pass.

**Status:** committed; actual GPU runtime regression not executed here.
