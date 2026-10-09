# LLM_CHA v0.2.32.2 — Dialogue-Guided Generation Integration

## Actual model connection
`dialogue_guided_generation_v02322.py` loads the real local LLM_CHA PyTorch checkpoint with `LanguageModel.load_checkpoint` from `model.py`, loads `Tokenizer.load` from `tokenizer_bpe.py`, and calls `LanguageModel.generate`. The adapter is separate from the existing large `chat.py` runtime (which has its own knowledge stores, guards, fallbacks and online training); this experiment does not claim to integrate all those subsystems.

DSS operations come from v0.2.32.1 `contextual_purpose_composition_v02321.step`.

Three comparable variants:
- `raw`: checkpoint generation from the user utterance only.
- `template`: deterministic DSS response, no neural generation.
- `guided`: same checkpoint, guided prompt including DSS topic, ordered purposes, relation, action and previous user/controller turns.

When DSS selects `ASK_CONFIRMATION` or `ASK_CLARIFICATION`, neither neural variant is called; questions belong to the controller and the skip is explicitly recorded. Other actions generate two separate checkpoint samples. Decoding is greedy by default (temperature 0).

This **does not** retrain the checkpoint to obey the new DSS instruction format; guidance may degrade output. Inspect the generated content instead of inferring success from successful API calls.

## Windows usage
```powershell
git fetch origin
git switch v0.2.32.2
git pull origin v0.2.32.2
python -m unittest -v test_dialogue_guided_generation_v02322.py
python dialogue_guided_generation_v02322.py --model model/model-llm-cha-response-quality-v0221.pt --tokenizer model/tokenizer-v0.7-bpe.json --show-prompts
python evaluate_dialogue_guided_generation_v02322.py --model model/model-llm-cha-response-quality-v0221.pt --tokenizer model/tokenizer-v0.7-bpe.json
```

Run a controller-only sanity check without checkpoint assets:
```powershell
python dialogue_guided_generation_v02322.py --controller-only
python evaluate_dialogue_guided_generation_v02322.py --controller-only
```

The model and tokenizer assets must be present locally. Supply alternative matching checkpoint/tokenizer paths with `--model` / `--tokenizer`; a mismatch fails explicitly. The generated evaluation file is `results/dialogue_guided_generation_v02322.json`.

## Inspect
Review per utterance:
1. Topic fidelity / retention across turns.
2. Fidelity to the selected goal, especially transitions and ordered plans.
3. Unsupported factual claims and malformed/repetitive output.
4. Japanese fluency.
5. Response latency and token count.
6. Whether guided generation is stronger or weaker than raw generation under the same generation parameters.

Evaluation outputs are **not independently scored**; there is no claim of higher neural generation quality without the Windows logs and human review.

## Next experiment
After comparing raw/template/guided outputs, consider checkpoint-level instruction tuning (preferably with disjoint holdout prompts), shorter DSS prompts for a small 512-token context, and integration with the main chat.py gate/knowledge pipeline.
