# LLM_CHA v0.3.7.7 — Normalized Means-Centric Persona Retrieval

The raw-corpus `v0.3.7.6` extraction candidates now have a common role structure: `subject`, `means`, `predicate`, `relation=MEANS_OF`, `original`, source/line/segment, and `factual_truth=NOT_ASSESSED`. The existing v0.3.7.5 licensed means lookup is checked first. When it misses, the normalized candidate path checks the same subject- and means-oriented question templates.

For unlicensed or unreviewed candidates, output is a **source-attributed quotation** prefixed with `persona>`. No automatically strengthened causative claim is made. Whitelisted v0.3.7.2 transformations may yield a `LICENSED_PARAPHRASE`. Explicit Truth Gate exclusions remain in effect. No corpus or checkpoint writes occur.

Limitations: fixed templates and crude regex role extraction can misparse literary language. The real-corpus audit observed **4 candidates (0 directly derivable)** under v0.3.7.6's rules, but these have not yet been manually adjudicated; do not treat them as validated semantic relations. This release broadens queryability of such candidates rather than claiming accurate general Japanese semantics. Performance measurements and review of the actual four source rows are next.

## Local verification

```powershell
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m unittest -v test_persona_normalized_means_v0377.py test_persona_means_audit_v0376.py test_persona_means_index_v0375.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
python chat.py
```

The new tests rely on a synthetic fixture. Verify actual `data/data-nagato.txt` matches separately before reporting real-world retrieval accuracy.
