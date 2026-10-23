# LLM_CHA v0.7.19 — Experimental Retrieval-Augmented Generation

The core architecture is unchanged: Trusted LLM owns Approved Semantic Memory,
while Experimental LLM owns PENDING Candidate Semantic Memory and the
Experimental Adapter. An explicitly permitted Trusted UNKNOWN may consult
Experimental knowledge; there is no automatic promotion.

This release adds a **standalone read-only RAG evaluation**. It retrieves
the best unambiguous pending Candidate using the v0.7.17 lexical matcher,
constructs a Japanese prompt containing the candidate question and answer,
and invokes the Experimental Adapter. Generated text is displayed only if it
is **exactly the candidate's registered answer**; otherwise the RAG answer
is rejected as UNKNOWN. Exact matching proves consistency with the
unverified candidate record, NOT factual truth.

The benchmark compares three approaches over the original eight v0.7.15
held-out paraphrase questions:
1. Evidence-only direct retrieval.
2. Adapter-only free generation.
3. Retrieval-augmented adapter generation.

Two unregistered questions are checked for rejection. Model weights,
production `chat.py`, and all knowledge stores are unmodified. This does
**not** yet integrate RAG into production runtime.

## PowerShell

```powershell
git fetch origin
git switch --track origin/v0.7.19
python -m unittest -v test_experimental_rag_v0719.py test_dual_path_v0718.py
python benchmark_rag_v0719.py
```

Output: `results/multi_fact_v0719/comparison.json`.

Interpret success carefully: direct evidence may win even when the
free-generating Experimental Adapter cannot replicate the answer under
a longer prompt. Do not infer improvements without GPU results.
