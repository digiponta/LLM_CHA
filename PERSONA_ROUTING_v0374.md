# LLM_CHA v0.3.7.4 — Persona Prompt Unification and Excerpt Relevance

The runtime now uses `persona>` for direct corpus-memory answers and grounded follow-ups whose provenance identifies `data-nagato.txt:subject-keyed-corpus-memory`. Other routes, including canonical CPU definitions, continue to show `AI>`. This changes the *visible attribution*, not the source truth status.

For `RAW_CORPUS_ONLY`, the automatic persona response now ranks up to 30 source-matching excerpts with a simple deterministic heuristic: prefer explicit subject mentions and substantive sentences; penalize short fragments. The selection remains literal concept matching, **not** a validated Japanese semantic parser nor a generative persona model. `MEANS_OF` derived paraphrases are not yet indexed into this retrieval path.

## Local verification

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m unittest -v test_persona_routing_v0374.py test_persona_semantic_memory_v0371.py test_auto_persona_route_v0373.py test_means_centric_semantics_v0372.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
python chat.py
```

With `LLM_CHA_MULTITOPIC=1` and `LLM_CHA_RETENTION_ACTIVE=1`, try: `宇宙とは`, `CPUとは`, `宇宙の話に戻って`, `もう少し詳しく`, `量子力学とは`, `数学とは`.

Expected: Nagato corpus answer and follow-ups use `persona>`, CPU uses `AI>`, and raw-only concepts use `persona>`. `【未検証の記録】` and evidence IDs/truth metadata continue to appear as before. Historical GPU harnesses may use `AI>` as part of their transcript filters; review failures for assertion compatibility versus actual semantic regressions. Do not declare the integration gate PASS before running it on the target machine.
