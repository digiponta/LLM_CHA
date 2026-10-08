# LLM_CHA v0.2.2 — Conversation Generalization & Gate Calibration

Development branch `v0.2.2`, based on `v0.2.1`.

## Implemented

- `conversation_quality_gate_v022.py`: a conservative **generated-answer-only** filter for mismatched thanks, fatigue, story requests, non-answers to book questions, and semantic-only rescue with very low lexical probe agreement.
- `chat.py`: enables the new filter by default; use `--no-conversation-quality-gate` for baseline comparison. It runs only after the standard generation gate, not in canonical/Semantic Memory retrieval routes.
- `test_conversation_quality_v022.py`: CPU-only synthetic tests.

**Scope limitation:** This is a heuristic safety net, **not** an empirical solution for linguistic quality or arbitrary semantic correctness. The threshold 0.15 is a provisional engineering heuristic, not calibrated against held-out distributions. The new guard does not fix the quality of raw generation; rejected responses can become `未学習です` rather than good conversational answers. Additional false-positive and false-negative analysis is required.

## Local validation

```powershell
git fetch origin
git switch --track origin/v0.2.2
python -m unittest -v test_conversation_quality_v022.py
python -m unittest -v test_conversation_replay_v021.py
python chat.py --model model/model-llm-cha-rpc-replay-v021.pt --tokenizer ..\LLM_TRY\model\tokenizer-v0.7-bpe.json --character nagato --temperature 0
```

Replay the old nine probes plus **unseen phrasings**, such as:

- お名前を伺えますか
- 自分が何者か説明して
- 今日はくたくたです
- 助かりました
- 最近、小説にはまっています
- 読書は楽しいと思う？
- 少しおしゃべりしませんか
- 昨日は科学の本を読んだ → その本は面白かった
- GPUの並列処理が速い理由を説明して

Run the same model with `--no-conversation-quality-gate` to compare rejection rates and identify false rejections. Do not add the evaluation prompts to replay training before measurement.

## Acceptance conditions

- Persona identity paraphrase retention evaluated on previously unseen phrasings, not only replay anchors.
- Accuracy and helpfulness scored manually, separately from token/semantic agreement.
- No false accepts for previously observed malformed responses.
- No regression in canonical, typed or conditional Semantic Memory, Truth-State and `/sleep`.
- No release/merge before local tests and runtime regression are reported.

**Status:** GitHub code committed; local GPU checkpoint unchanged; full regression and held-out evaluation are not yet executed.
