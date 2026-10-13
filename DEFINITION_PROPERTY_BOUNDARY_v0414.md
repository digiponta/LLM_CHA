# LLM_CHA v0.4.14 — Definition / Property / Attribution / Context Boundary

v0.4.14 adds **read-only, heuristic exploratory classification**, separate from the frozen v0.4.12 extractor. It examines literal sentences, classifying as `DEFINITION_CANDIDATE`, `PROPERTY`, `ATTRIBUTED_CLAIM`, `CONTEXT_DEPENDENT`, or `UNRESOLVED`. Retains source spans and reports `UNVERIFIED` / `PENDING_REVIEW`; classification **does not imply factual truth** or an approved definition.

The diagnostic highlights v0.4.13 cases: h09 (`という` naming) and h10 (`とされる` attribution) require distinct treatment; h29 (`広大である`) is property, not taxonomy. **Known limitation:** h19 has a first isolated positive-looking sentence followed by a qualifier (`しかし`) in a *second sentence*. This classifier marks the second sentence as context but does **not** retroactively invalidate or downgrade the first one. It is a deliberately unresolved cross-sentence scope problem. Another limitation: lexical phrase guards are illustrative; not general Japanese syntactic or semantic inference. Do not promote results or interpret them as safe for production knowledge ingestion.

`evaluate_definition_boundary_v0414.py` retrospectively scores the previously frozen 30 examples (not a new blind holdout) and shows individual disagreements. **No changes** to the v0.4.12 extraction code, prior v0.4.13 fixture, Truth Gate, Semantic Memory, persona, corpus, `chat.py`, model, or `/sleep`.

## Verify locally

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_definition_property_boundary_v0414.py test_evaluate_proposition_holdout_v0413.py test_article_proposition_alignment_v0412.py
python evaluate_definition_boundary_v0414.py --report results/definition_boundary_v0414.json
python definition_property_boundary_v0414.py --evidence results/wikipedia_article_evidence_v0409_novel.json --report results/definition_boundary_novel_v0414.json
python verify_integration_v0366.py --gpu --legacy --timeout 240
```

Next: independently annotate genuinely separate examples and implement cross-sentence scope tracking with explicit review policy, rather than claiming resolved h19 or universal definition/property correctness.
