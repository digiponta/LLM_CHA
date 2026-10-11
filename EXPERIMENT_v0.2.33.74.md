# LLM_CHA v0.2.33.74 — Generated Response Quality Gate (Greeting Pilot)

Based on the v0.2.33.73 user GPU log: `こんにちは` was routed as a greeting but the generative candidate was incoherent and the response gate returned `未学習です`. The new guard detects **whole-turn standalone greetings only** and substitutes a short, known-appropriate conversational response when generation was rejected, empty, excessively long or otherwise evidently malformed.

The guard is applied to the final surface response, **after** the existing model gate and routing logic. This means the original gate may still record a review item, so this is **not yet a full repair of gate misclassification or queue side effects**. The quality heuristic may miss some fluent-but-incoherent short greetings. Mixed greeting+factual questions, reference questions and all truth-gated corpus queries remain untouched. This is a deterministic fallback, not neural-model learning or evidence of improved raw generation.

## Run on Windows

```powershell
git fetch origin
git switch v0.2.33.74
git pull origin v0.2.33.74
python -m py_compile chat.py generated_response_quality_v023374.py
python -m unittest -v test_generated_response_quality_v023374.py test_truth_aware_corpus_gate_v023373.py
python chat.py --session-reference-memory
```

For GPU runtime, enter `こんにちは`, `こんばんは`, `こんにちは、宇宙について教えて`, `宇宙とは`, `量子力学とは`, `/exit`. Expected: standalone greetings yield short natural responses, whereas `宇宙とは` remains blocked when UNVERIFIED. The mixed greeting/factual sentence must not use the greeting-only fallback, though its resulting generation is otherwise not guaranteed.

No Truth State, model weights, or Semantic Memory records are changed by this branch. Tests are committed and awaiting actual execution.
