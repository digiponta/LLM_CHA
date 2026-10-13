# LLM_CHA v0.3.7.5 — Bidirectional Means-Centric Persona Retrieval

Experimental, read-only, source-attributed indexing of explicitly recognized `Subject は Means によって Predicate` statements.

## Example (fixture)

Source: `私は数学によって問題を解く。`

- `数学は何をするもの？` -> `persona> 数学は私に問題を解かせる。`
- `私は何によって問題を解く？` -> `persona> 私は数学によって問題を解く`

Both directions use the same source row and `MEANS_OF` roles, with line/segment provenance. `factual_truth=NOT_ASSESSED` and no modification to corpus, Truth Gate, or LLM weights. The previous regular subject-memory and canonical answer paths remain in place.

**Limitations:** Only v0.3.7.2's small list of licensed predicates and narrow query templates are recognized. No training and no general-purpose semantic parser. The source corpus might contain zero matching patterns, so a real-corpus HIT is not promised; the tests use a controlled fixture. Existing corpus-memory retrieval can still take precedence for some question types. Explicit truth blocks remain effective. This is a first means-index connector, not universal bidirectional semantic retrieval.

## Run in PowerShell

```powershell
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m unittest -v test_persona_means_index_v0375.py test_persona_routing_v0374.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
python chat.py
```

If `data-nagato.txt` contains a recognized sentence, try `数学は何をするもの？` and `私は何によって問題を解く？`. Otherwise these questions follow the previous runtime paths, unchanged.
