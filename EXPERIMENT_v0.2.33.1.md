# LLM_CHA v0.2.33.1 — Semantic Curriculum Builder

This experiment tests whether **progressively training response initiation, prefix-conditioned continuation and full answer prediction** changes free generation compared with a conventional SFT baseline. Both arms start with the same frozen checkpoint, train on the same reviewed Semantic Memory expansion rows, use the same learning rates and replay samples, and take the **same total number of optimizer steps**.

## Stages and definitions
- Steps 0–29%: **initiation**: NLL over first 25% of teacher answer tokens, plus 0.2× full-answer NLL.
- Steps 30–64%: **continuation**: NLL over answer suffix with the first 25% gold tokens given as context, plus 0.4× full-answer NLL.
- Steps 65–100%: **full**: all teacher answer tokens.
- Baseline: full-answer NLL on every step.

The continuation term is still **teacher forced**; it does not automatically improve self-generated long text. The paired arms are equal in *optimizer updates*, but curriculum performs extra forward passes and uses different weights, so FLOPs and effective token-loss contributions are not perfectly matched. The corpus is tiny and the generated examples share response templates.

## Commands (PowerShell)

```powershell
git fetch origin
git switch v0.2.33.1
git pull origin v0.2.33.1

python -m unittest -v test_semantic_curriculum_v02331.py
python train_semantic_curriculum_v02331.py --steps 48
python evaluate_semantic_curriculum_v02331.py
```

Inputs: `data/semantic_expansion_v02328.jsonl` (approved records; do not re-export after approval), `model/model-llm-cha-response-quality-v0221.pt`, matching BPE tokenizer.

Generated:
- `model/model-llm-cha-curriculum-baseline-v02331.pt`
- `model/model-llm-cha-curriculum-staged-v02331.pt`
- `results/semantic_curriculum_train_v02331.json`
- `results/semantic_curriculum_eval_v02331.json`

## Interpret with care
The output comparison uses the exploratory unseen/control/legacy probes from v0.2.32.7. These were already inspected and **are not untouched final test data**. The evaluation includes both raw (no DSS purpose labels) and Short conditional prompts where applicable, with greedy decoding. Assess manually whether answers are correct, on-topic, purpose-aligned and fluent, including retention.

**No promotion** to INTERNALIZED and no automatic route switching. If initiation accuracy improves without answer completion, the next focus should be stronger continuation supervision or a generation-side semantic bridge rather than assuming internalization. All experiments keep the base model intact.
