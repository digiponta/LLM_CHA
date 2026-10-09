# LLM_CHA v0.2.18 — Japanese Foundation + Dialogue SFT Pilot

Goal: test whether a small language-model continuation stage, followed by dialogue SFT, improves both Japanese sentence quality and conversational relevance. **No trained weights or GPU validation are committed.**

## Two-stage controlled experiment

1. `prepare_japanese_foundation_v0218.py` derives a small Japanese-text corpus from the **v0.2.12 training split only**. Defaults to 5,000 rows. Validation and test dialogue files are NEVER used here; the raw LM trainer makes an internal 10% validation split. The corpus is dialogue-derived, **not independent high-quality literary prose**, so treat this as a pilot, not full Japanese language pretraining.
2. `train_foundation_dialogue_v0218.py --stage cpt` runs the existing `train_nagato.py` for 1 epoch, LR=5e-6, using a separate `model/model-llm-cha-foundation-v0218.pt` output.
3. `--stage sft` runs the existing `train_nagato_chat.py` against the v0.2.12 diverse dialogue train/val splits, replaying the original persona anchors, and writes `model/model-llm-cha-foundation-dialogue-v0218.pt`.
4. Baselines (v0.2.8, v0.2.11, v0.2.12) remain unchanged; use Greedy decoding because v0.2.17's 270 AI ratings penalized higher-temperature sampling.

## Commands (PowerShell)

```powershell
git fetch origin
git switch --track origin/v0.2.18
python -m unittest -v test_foundation_v0218.py
python prepare_japanese_foundation_v0218.py
python train_foundation_dialogue_v0218.py --dry-run
python train_foundation_dialogue_v0218.py
```

To compare held-out assistant NLL on identical rows:

```powershell
python diagnose_models_v0213.py --max-rows 1000 --models model/model-llm-cha-quality-v028.pt model/model-llm-cha-generalization-v0212.pt model/model-llm-cha-foundation-dialogue-v0218.pt --output results/foundation_comparison_v0218.json
```

Also compare actual generated answers with Greedy using identical prompts and human blind review, not merely NLL. Check persona, CPU canonical retrieval, Truth-State, Unknown Gate, Semantic Memory and `/sleep` separately.

## Decision rule

Only increase raw LM training if the two-stage candidate improves held-out Japanese generation **and** dialogue relevance without raising malformed/meaningless response rate. Lower NLL alone is not enough. Controlled ablation requires a matched **SFT-only** baseline (v0.2.12), same prompts, and same decoding. The training corpus is selected from a subset of SFT train and might teach the same domain; it does not prove broad generalization. Unknown false facts from external sources must not be used as automatically verified knowledge.

The v0.2.17 quality scores are AI rubric ratings, not independent human agreement; evaluate any close results cautiously.
