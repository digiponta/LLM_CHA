# v0.2.33.75 — Multi-Intent & Natural Reference Resolution (pilot)

Based on the GPU log from v0.2.33.74.1, `こんにちは、宇宙について教えて` was incorrectly classified as `greeting` and fell through to `GATE_REVIEW`. A separate previously observed `昨日の続き` yielded `未学習です` instead of requesting clarification.

This pilot conservatively normalizes an exact greeting + single subject query into `Xとは` *before* the existing Retrieval-First and Truth-Aware knowledge pipeline; e.g. `こんにちは、宇宙について教えて` → `宇宙とは`. The model must not answer the unverified corpus merely because a greeting precedes the question. A small explicit set of ambiguous reference-only phrases prompts the user for a specific topic. This is clarification **not** reference resolution or automatic approval. If a reference confirmation is already pending, this clarification shortcut yields to the existing reference bridge.

## Windows

```powershell
git fetch origin
git switch v0.2.33.75
git pull origin v0.2.33.75
python -m py_compile chat.py multi_intent_reference_v023375.py
python -m unittest -v test_multi_intent_reference_v023375.py test_greeting_hardening_v0233741.py test_truth_aware_corpus_gate_v023373.py
python chat.py --session-reference-memory
```

Enter: `こんにちは`, `こんにちは、宇宙について教えて`, `宇宙とは`, `昨日の続き`, `あの実験`, `/exit`. Expect direct corpus memory to remain blocked for UNVERIFIED. Expect an explicit clarification for the ambiguous reference phrase, not a fabricated continuation.

**Limitations:** Multi-intent recognition is deliberately narrow and only rewrites explicit single-subject patterns. Unsupported compound intents still use existing behavior. It does not guarantee that any arbitrary knowledge query is verified; other answer pipelines still require separate safety auditing. No model retraining, reference auto-confirmation or Truth State changes. Tests are committed, not yet executed on the user's system.
