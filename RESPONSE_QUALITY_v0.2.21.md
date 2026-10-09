# LLM_CHA v0.2.21 — Context-Aware Response Quality SFT

Goal: improve conversational specificity and context-dependent followups by **training the model**, rather than relaxing the semantic/truth gate or further tuning candidate ranking.

## Data and protocol

- Six manually authored four-turn TRAIN scenarios: science-fiction novels, historical novels, mountain hiking, classical music, cooking, programming.
- Two manually authored four-turn HOLDOUT scenarios: photography and gardening.
- Prompts use the existing `人: …\nAI: …` chronological dialogue format. Targets are assistant responses only.
- Repeat the 24 distinctive training-turn examples 12 times; mix 4,000 examples from the existing **v0.2.12 train split**, excluding photo/garden keywords. This is a pilot and repeated data can overfit.
- Validation includes **only the 8 heldout synthetic turns**. Small validation results have high uncertainty; the synthetic holdout and broad dialogue test are complementary. Do not train on holdout examples.
- Fine-tune the local `model/model-llm-cha-foundation-dialogue-v0218.pt` model with low LR and retain original v0.2.18 weights. Greedy decoding remains the default.

## PowerShell

```powershell
git fetch origin
git switch --track origin/v0.2.21
python -m unittest -v test_response_quality_v0221.py
python prepare_response_quality_v0221.py
python train_response_quality_v0221.py --dry-run
python train_response_quality_v0221.py
```

Then compare with the v0.2.18 baseline on the same independent dialogue test:

```powershell
python diagnose_models_v0213.py --max-rows 1000 --models model/model-llm-cha-foundation-dialogue-v0218.pt model/model-llm-cha-response-quality-v0221.pt --output results/response_quality_comparison_v0221.json
```

Run two separate chats with `--dialogue-history-turns 2 --show-context --show-candidate-ranking` and each checkpoint; use the same sequence: `こんにちは`, `最近、SF小説を読んでいます`, `その話を続けて`, `長門有希について教えて`. Real qualitative success means a coherent topic-specific reply and meaningful continuation, not simply a better synthetic validation loss or acceptance rate. Preserve unknown/truth safeguards.

This SFT supplies *positive examples*; it does not implement preference optimization or negative-example loss. Avoid interpreting a lower teacher-forced NLL as guaranteed improved free generation. No local GPU experiment has been executed by the GitHub changes.
