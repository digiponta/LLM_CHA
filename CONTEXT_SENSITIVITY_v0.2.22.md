# LLM_CHA v0.2.22 — Context Sensitivity & Semantic Grounding Evaluation

This is a **diagnostic-only** branch: no weight training and no runtime gate changes.

## Controlled evaluation

The same user question, `その話を続けて`, is tested with four prompts: SF/space-exploration, cooking/curry, classical music, and **no history**. For each of v0.2.18 and v0.2.21 checkpoints, the script measures:

1. **Training/model likelihood:** teacher-forced per-token NLL of topic-specific reference answer with full history vs no history. Positive `nll_gain` means the reference became more likely with that context; this is not a generation-quality score.
2. **Generation:** raw Greedy output and two temperature-0.7 candidates, without the chat gates. Each candidate is preserved in the report.
3. **Grounding proxy:** exact topic-keyword presence in generated text. This does not capture paraphrases or entailment; absence alone is not proof of semantic failure.
4. **Selection ablation:** evaluate the existing v0.2.20 candidate reranker on the three generated texts with **neutralized model confidence**. This diagnoses text-feature selection only. It is **not** an end-to-end chat result.

## Run on Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.2.22
python -m unittest -v test_context_sensitivity_v0222.py
python evaluate_context_sensitivity_v0222.py
```

Full report: `results/context_sensitivity_v0222.json`.

## Interpret

- Positive reference NLL context gain but topic-free generations: context may be encoded but not expressed by the decoder / short answer distribution; examine Greedy vs sampled responses.
- Near-zero or negative context gains for all scenarios: insufficient evidence that the model leverages history; examine training/preformat consistency.
- Topic-matched sample candidate exists but wrong candidate selected: review text ranking, confidence filtering, and the downstream gates independently.
- No samples discuss the topic: reranking alone cannot fix generation; improve response supervision/data.
- No-history response should request clarification, not invent a past topic.

**Limitations:** just 4 hand-crafted prompts and synthetic references; quality judgments need more unseen scenarios and blind human/AI rating. No statistical claim of generality. The two training checkpoints may differ in how many examples they have seen. Also compare against the untouched v0.2.12 common heldout NLL if the pilot shows improvements.
