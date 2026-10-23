# LLM_CHA v0.7.17 — Candidate Memory Retrieval Experiment

This release adds a **standalone evaluation**, not a change to the production
Trusted-first router or the Experimental Adapter weights.

- Read PENDING facts only from Experimental Candidate Semantic Memory.
- Match short Japanese question paraphrases using candidate-discriminative
  character trigrams.
- Reject queries with no distinctive matching n-gram, or a tied best match.
- Return candidate text tagged `EXPERIMENTAL_UNVERIFIED`, with source and
  candidate ID; never promote or write approved data.
- Use the original 8 v0.7.15 holdout paraphrases without adding them to training.

This is **lexical retrieval**, not embedding-based semantic understanding.
It may fail on synonyms or accept a false match. Retrieval consistency is not
evidence of factual correctness, and text from unapproved knowledge must remain
clearly labeled.

## Windows
```powershell
git fetch origin
git switch --track origin/v0.7.17
python -m unittest -v test_semantic_retrieval_v0717.py test_paraphrase_diagnostics_v0716.py
python evaluate_semantic_retrieval_v0717.py
```

By default this evaluates the isolated dataset under
`results/multi_fact_v0715/dataset/` and writes
`results/multi_fact_v0717/retrieval.json`.

**Current status:** The previous 4/4 training-memory and 0/8 free-generation
holdout baselines remain unchanged. The new lexical Candidate retrieval is an
experimental alternative route and has not yet been integrated into `chat.py`.
Future comparisons should evaluate the same questions for Adapter-only,
Candidate-retrieval-only and combined generation, including false accepts and
Approved protection.
