# LLM_CHA v0.2.33.59 — Structural Semantic Consistency Validation

Adds `/refstructural` to the opt-in `chat.py` reference subsystem.

The validator parses a deliberately **restricted** Japanese proposition grammar: `XはYである/ではない`, `XはYを含む/含まない`, `XはYに適する/適さない`, optionally prefixed by `条件Cでは`. It compares relation, ordered arguments, polarity and condition, and fails closed on unsupported grammar. The normal evidence gate (TRUE, appropriate Knowledge State, dispatcher action, source metadata) runs first.

## Windows PowerShell
```powershell
git fetch origin
git switch v0.2.33.59
git pull origin v0.2.33.59
python -m py_compile chat.py structural_semantic_consistency_v023359.py
python -m unittest -v test_structural_semantic_consistency_v023359.py test_evidence_answer_consistency_v023358.py
python chat.py --session-reference-memory
```

After approving the reference and mapping as in v0.2.33.56, compare `/refconsistent` and `/refstructural`. The current `RAW_CORPUS_ONLY / UNVERIFIED` path will remain blocked before structural comparison; positive/negative structural cases are covered by isolated fixtures.

This gate is **not a general Japanese parser**, not a proof of factual correctness, and does not infer meaning from arbitrary natural language. It does not write Semantic Memory or train the LLM. Branch not merged into main.
