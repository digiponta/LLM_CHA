# v0.13.58.82.96 RealPersonaChat pilot

The Windows preflight reported READY for 2286 pairs, with dataset SHA-256 edb195b62a06daf02b52f4a2c93d3974dadcd4c8947ec83e49a469c0096de461.

Windows PowerShell:

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.96-real-persona-sft
python -m unittest -v test_real_persona_train_v013588296.py test_real_persona_training_preflight_v013588295.py

# Preview only (no training):
python train_real_persona_pilot_v013588296.py --tokenizer C:\Users\inoma\git\misc\LLM_GPU\model\tokenizer-v0.7-bpe.json

# Explicitly start separate pilot training after preview:
python train_real_persona_pilot_v013588296.py --tokenizer C:\Users\inoma\git\misc\LLM_GPU\model\tokenizer-v0.7-bpe.json --execute
```

Uses two epochs, learning rate 1e-5, manual weight 1; writes only model/real-persona-cp-pilot-v013588296.pt and results/real-persona-cp-state-v013588296.json. Existing production checkpoints are untouched by the launcher. The checkpoint and state target must not already exist. Test five daily conversation holdout prompts and two semantic retrieval questions before any model promotion. Existing online_train.py internally uses pair-level validation, so its validation loss is not a dialogue-independent estimate of generalization. Evaluate separately using held-out dialogues.
