# LLM_CHA v0.3.4 — Multiple Important Topic Competition

Branch: `v0.3.0`. Stable Release: `v0.2.34` (unchanged).

Five new deterministic synthetic scenarios examine contention among important topics:
old versus newly important, recently used versus stale, high-frequency versus new, revisiting after reallocation, and explicit protection. For capacities 2, 4, 8 compare v0.3.1 Hybrid against v0.3.3 protected Auto-Pin with age thresholds 4, 8, 16: **60 experimental result rows**.

We measure important-topic query hit rate, ordinary query hit rate, promotion/demotion and refusals, capacity and budget compliance. Benchmark is deliberately read-only regarding Corpus, Truth State and Semantic Memory. Labels are hand-coded; results do not represent actual conversation quality.

Run:
```powershell
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m unittest -v test_adaptive_context_v023350.py test_adaptive_retention_eval_v023351.py test_retention_cross_scenario_v0300.py test_hybrid_retention_v0310.py test_adaptive_importance_v0320.py test_auto_pin_protection_v0330.py test_important_competition_v0340.py
python important_competition_v0340.py
```

Expected 68 total tests (prior 58 plus 10 new), pending user execution. Report `results/important_competition_v0340.json`.

Next: evaluate tradeoffs, introduce holdout traces and an explicit admission metric before any chat.py feature-flag integration. Do not change Truth-Gate permissions as part of retention policy.
