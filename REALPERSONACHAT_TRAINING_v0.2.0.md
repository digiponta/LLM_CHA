# LLM_CHA RealPersonaChat general conversation SFT (v0.2.0 experiment)

## Source and license

- Source: https://github.com/nu-dialogue/real-persona-chat
- RealPersonaChat by Yamashita et al., PACLIC 2023.
- Dataset license: **CC BY-SA 4.0**, distinct from LLM_CHA repository code licensing.
- Dataset contains real speakers' persona/demographic material: do not identify, impersonate, or publish individual speaker profiles.
- This pipeline **does not import** speaker metadata, Big Five scores, demographics, or profiles as a character; it uses anonymized dialogue turns only.
- Review redistribution, attribution, and share-alike duties before publishing transformed datasets or trained checkpoints. Training alone does not settle legal status of distributed weights.

## 1. Download the source dataset (local machine)

```powershell
git clone https://github.com/nu-dialogue/real-persona-chat.git data-src/real-persona-chat
```

Expected directory: `data-src/real-persona-chat/real_persona_chat/dialogues`. If its structure differs, locate the actual dialogues directory and use that path.

## 2. Convert into SFT dialogue pairs

```powershell
python prepare_realpersonachat_v020.py --dialogues data-src/real-persona-chat/real_persona_chat/dialogues --output data/realpersonachat
```

For a small pilot, add `--max-dialogues 1000`. The converter creates:
- `rpc_train.jsonl`, `rpc_val.jsonl`, `rpc_test.jsonl`
- `rpc_manifest.json`

Splitting is deterministic **per dialogue**, not per utterance. Speaker profile metadata is not included. Masked turns and overly long turns are excluded. Output pairs have `user` and `assistant` fields compatible with `train_nagato_chat.py`.

## 3. Confirm models before training

```powershell
Test-Path ..\LLM_TRY\model\model-llm-try-nagato-chat-v94.pt
Test-Path ..\LLM_TRY\model\tokenizer-v0.7-bpe.json
```

If `LLM_TRY` contains them, use explicit paths; no checkpoint copying is needed.

## 4. Train a separate checkpoint (RTX 3070 Ti)

```powershell
python train_realpersonachat_v020.py --base-model ..\LLM_TRY\model\model-llm-try-nagato-chat-v94.pt --tokenizer ..\LLM_TRY\model\tokenizer-v0.7-bpe.json --output model/model-llm-cha-rpc-v020.pt --epochs 3 --batch-size 8
```

The training wrapper reuses assistant-target-only SFT and keeps the input checkpoint unchanged. Use `--dry-run` to check the command without training.

## 5. Verify before accepting the checkpoint

```powershell
python -m unittest -v test_realpersonachat_v020.py
python chat.py --model model/model-llm-cha-rpc-v020.pt --tokenizer ..\LLM_TRY\model\tokenizer-v0.7-bpe.json --character nagato
```

Compare general conversation responses with the original checkpoint and run the existing Semantic Memory / truth-state / `/sleep` regression suites. The `--character nagato` profile only changes the displayed speaker label in v0.1.0; it does not yet change generation style.

## Status

- Converter, training wrapper, tests: committed.
- Dataset download: **not executed in GitHub**.
- GPU training: **not executed**.
- Checkpoint: **not produced**.
- Independent held-out performance / catastrophic forgetting: **not measured**.

Do not merge into main or label a stable release until the local test and evaluation results have been inspected.
