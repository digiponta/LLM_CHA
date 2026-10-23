# LLM_CHA v0.7.20 — Experimental Memory-First

Standalone, read-only experiment. Trusted LLM remains authoritative over
Approved knowledge. On a structured Trusted UNKNOWN **with explicit opt-in**,
Candidate Semantic Memory is searched. The selected pending Candidate and
provenance determine the unapproved answer.

Two modes:
- `evidence`: return matching Candidate answer, tagged
  `EXPERIMENTAL_UNVERIFIED`, without generation.
- `constrained`: also send retrieved Candidate knowledge to Experimental
  Adapter; compare generation to exact candidate answer. If different,
  classify the generation as rejected and **retain the candidate evidence**
  (never expose mismatched generated text as the answer).

Unknown/ambiguous questions return UNKNOWN; no automatic promotion,
Approved-store writes, or Trusted-weight modification.

## PowerShell
```powershell
git fetch origin
git switch --track origin/v0.7.20
python -m unittest -v test_experimental_memory_first_v0720.py test_experimental_rag_v0719.py
python benchmark_memory_first_v0720.py --mode evidence --output results/multi_fact_v0720/evidence.json
python benchmark_memory_first_v0720.py --mode constrained --output results/multi_fact_v0720/constrained.json
```

The benchmark uses the original eight held-out synthetic paraphrases and
two absent questions. This is not factual truth validation, a statistically
robust generalization result, or production chat.py integration. The Trusted
response is a structured stub returning UNKNOWN in this benchmark; actual
Trusted retention has not been evaluated. Prompt augmentation alone previously
yielded 0/8 exact in v0.7.19, so constrained mode may again reject all model
generations while delivering registered unapproved evidence correctly.
