# LLM_CHA v0.7.18 — Two Experimental Knowledge Answer Paths

Preserve the architectural separation:
- **Trusted LLM:** Approved Semantic Memory + Trusted Adapter.
- **Experimental LLM:** PENDING Candidate Semantic Memory + Experimental Adapter.

After a permitted Trusted UNKNOWN, the Experimental side can operate in
three explicitly selected modes:

- `evidence`: select an unambiguous PENDING Candidate and show its
  registered answer with `EXPERIMENTAL_UNVERIFIED` provenance.
- `adapter`: select a Candidate and invoke the Experimental Adapter;
  display only if its generated text exactly reproduces that Candidate's
  registered answer; otherwise reject.
- `compare`: evaluate both methods separately, never automatically
  choosing a more trusted answer.

Both paths reject absent/ambiguous Candidate matches, prohibit automatic
knowledge approval, and leave Trusted weights/Approved memory unchanged.
Retrieval uses v0.7.17's lexical character 3-gram matcher, not semantic
embeddings. This release does **not modify production chat.py routing**.

## PowerShell

```powershell
git fetch origin
git switch --track origin/v0.7.18
python -m unittest -v test_dual_path_v0718.py test_semantic_retrieval_v0717.py
python benchmark_dual_path_v0718.py
```

Output: `results/multi_fact_v0718/comparison.json`.

Benchmark reuses the original eight v0.7.15 held-out paraphrases and the
separate four-fact Experimental checkpoint. Accuracy in retrieving a
synthetic Candidate is **not verification of factual correctness**.
Next: assess lexical false matches and build a safe production integration
hook restricted to Trusted UNKNOWN states.
