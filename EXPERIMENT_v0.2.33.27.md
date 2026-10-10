# LLM_CHA v0.2.33.27 — Pointer Position Curriculum Analysis

## Motivation

At v0.2.33.26, all three heads yielded **0/40** exact free copies on long sequences (12–18 IDs). Their teacher-forced pointer-position accuracy was only **45–47%**, compared with ~83–85% for short sequences. Short-validation checkpoint selection chose **Stage 2** for every head, leaving the long-sequence properties of Stage 3 uncertain.

## Experiment

The frozen backbone is `model/model-llm-cha-algorithmic-copy-v023320.pt`. Recreate three heads (Pointer-only, Hybrid, Adaptive), each with the same random seed, data, training order and learning rate as the v0.2.33.26 protocol.

Each arm trains three stages, **saving all three checkpoints rather than saving only the best**:
- Stage 1: 200 sequences, length 2–8.
- Stage 2: 200 sequences, length 2–18.
- Stage 3: another pass on the same 200 long-range examples.

Use two **separate, independent validation groups**, both generated before training:
- short: 40 sequences, length 2–8;
- long: 40 sequences, length 12–18, disjoint from the short validation, all training, and every evaluation group.

For every Stage and arm, collect both validation losses, equal-weight balanced validation loss, free exact-copy results, teacher-forced pointer-position accuracy including EOS, position-by-position accuracy, and split by input sequences with vs without repeated tokens.

Report the stage selected by (1) short-only validation and (2) balanced short-plus-long validation. Both are fixed in advance; **never select by test/OOD performance**. Stage 3 is evaluated and preserved regardless of selection.

## Windows commands

```powershell
git fetch origin
git switch v0.2.33.27
git pull origin v0.2.33.27
python -m py_compile pointer_position_curriculum_v023327.py
python -m unittest -v test_pointer_position_curriculum_v023327.py
python pointer_position_curriculum_v023327.py
```

Outputs:
- `results/pointer_position_curriculum_v023327.json`
- Nine stage checkpoints under `model/pointer_position_curriculum_v023327/`.

The script refuses to overwrite existing outputs. The evaluation may take substantial GPU time because it analyzes each stage and each position independently.

## Interpretation

Compare long-position accuracy for stages 1, 2 and 3. If Stage 3 improves long-position accuracy while short-only validation worsens, that supports a checkpoint-selection tradeoff. If all stages remain weak on long sequences, longer and richer position supervision or a new position-alignment mechanism will be the next research directions.

Teacher-forced pointer-position accuracy is separate from autonomous exact-copy performance. When source IDs repeat, predicting one of multiple positions with the same ID can yield correct output tokens even if the designated positional label is missed. The base model, DSS, Semantic Memory and Semantic Bridge remain unchanged.
