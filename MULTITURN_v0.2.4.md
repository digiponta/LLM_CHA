# LLM_CHA v0.2.4 — Multi-turn Dialogue Learning Pilot

Development branch `v0.2.4`. New checkpoint is produced **only after local training**.

## Approach

- Multi-turn examples preserve chat.py's actual `人: ...\nAI: ...\n人: ...\nAI:` format.
- Conversation-group train/val/test partition follows existing deterministic RealPersonaChat split.
- The trainer's new `--preformatted-prompts` mode prevents double `人:` prefixes and preserves assistant-target-only loss.
- The runtime's `--dialogue-history-turns N` opt-in activates chronological history for non-definition, non-comparison, non-internalized character generation; default 0 preserves earlier behavior.
- Verified Semantic Memory lookups, truth state, knowledge queues, and `/sleep` paths remain unchanged.
- Pilot trains a **new** checkpoint with small LR from the v0.2.1 persona-replay checkpoint. It does not overwrite base weights.

## Commands (PowerShell)

```powershell
git fetch origin
git switch --track origin/v0.2.4
python -m unittest -v test_multiturn_v024.py test_conversation_intent_v023.py test_conversation_quality_v022.py
python prepare_multiturn_v024.py --max-dialogues 1000 --history-turns 2
python train_multiturn_v024.py --dry-run
python train_multiturn_v024.py
python chat.py --model model/model-llm-cha-multiturn-v024.pt --tokenizer ..\LLM_TRY\model\tokenizer-v0.7-bpe.json --character nagato --dialogue-history-turns 2 --temperature 0
```

Suggested sequence: `最近、小説にはまっています` → `SFです` → `その話、続けて`. Also test `CPUとは`, unknown GPU questions, identity paraphrases, `/reset`, and `/sleep status`.

## Limitations and evaluation

- Multi-turn SFT input truncation depends on the original model's context length 512.
- No fixed answer prompts in test split are automatically evaluated by this release.
- Only the last accepted turns enter conversation history. Profile-routed intents can appear there, but they are not accepted as approved factual memory.
- Changing conversation history can alter model-based answers and may introduce false positives. Compare with `--dialogue-history-turns 0`.
- The converter excludes multi-speaker non-alternating windows; this reduces data but avoids ambiguous roles.
- Because the base checkpoint has persona replay, perform a held-out persona/knowledge regression before adopting the new weights.

Status: code committed; dataset conversion, tests, GPU SFT and quality improvement **not yet verified locally**.
