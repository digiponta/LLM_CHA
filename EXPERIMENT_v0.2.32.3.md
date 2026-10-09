# LLM_CHA v0.2.32.3 — Purpose Prompt Ablation

This branch compares three **real-checkpoint** generation prompt variants with the same frozen model and decoding settings. It does **not** fine-tune the model, claim improved generation, or modify the v0.2.32.2 baseline.

| Condition | Prompt |
|---|---|
| raw | `人: <utterance>\nAI:` |
| short | `話題: <topic>\n目的: <purpose>\n人: <utterance>\nAI:` |
| full | v0.2.32.2 full DSS including relation, action, instructions, and available history |

The controller still handles ASK actions without checkpoint calls. Seven dialogue scenarios include learning, development, troubleshooting, casual, contextual reference, sequential planning, and confirmation. Each generated output stores the model source, token count, time, and prompt length.

## Windows commands

```powershell
git fetch origin
git switch v0.2.32.3
git pull origin v0.2.32.3
python -m unittest -v test_purpose_prompt_ablation_v02323.py
python purpose_prompt_ablation_v02323.py --model model/model-llm-cha-response-quality-v0221.pt --tokenizer model/tokenizer-v0.7-bpe.json
```

For control-flow tests without checkpoints:

```powershell
python purpose_prompt_ablation_v02323.py --controller-only
```

Review `results/purpose_prompt_ablation_v02323.json` for each variant. Assess topical relevance, purpose fidelity, Japanese quality, hallucination/repetition, and latency. Do not treat short model outputs or faster inference as quality improvements. Greedy decoding reduces sampling noise but does not fully eliminate hardware/software effects on latency.

## Next: Purpose-Conditioned SFT design

Only after ablation results are examined, define a training corpus with **disjoint train/validation/test topics and paraphrases**, paired exact inference-format prompts, canonical response targets, negative/rejected examples, and replay protection of existing chat behavior. Retain frozen model as the baseline; first train an experimental checkpoint on a new branch and evaluate action and answer quality separately. Long DSS prompts may exceed the useful distribution/context of this small model; shortening alone is not a learned improvement.

## Known boundaries

- This is a separate standalone inference adapter, not a modification of the large `chat.py` runtime and its existing safety/semantic gates.
- The checkpoint/tokenizer pair must match the ones used in training.
- No automatic claim of purpose understanding is derived from strings in prompts.
- The scenario set is hand-authored exploratory evidence, not a broad unseen benchmark.
