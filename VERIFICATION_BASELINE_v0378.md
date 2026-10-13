# LLM_CHA v0.3.7.8 — Integration-Verified Baseline (2026-10-13)

**Disposition:** Preserve as an **integration-verified experimental baseline**, not a formal stable release and not a claim of semantic extraction accuracy.

## User-reported verification (RTX 3070 Ti)

- `python -m unittest -v test_persona_review_v0378.py test_persona_normalized_means_v0377.py`: **20/20 PASS**.
- `python verify_integration_v0366.py --gpu --legacy --timeout 240`: **264/264 unified unit tests PASS**, `RECOVERY_GPU`, `SHADOW_GPU`, `ACTIVE_GPU`, `REVISIT_GPU`, and `LEGACY` all PASS, culminating in `INTEGRATION_GATE_V0366_PASS`.
- `python persona_review_v0378.py --corpus data/data-nagato.txt`: **4 extracted candidates**, 8 generated source-query probes, **8/8 exact-source hits** (`source_hit_rate=1.0`); **0 human reviewed**; `precision=null`.
- Source extraction covers narrow `MEANS_OF` forms. Neither a semantic-role precision number nor independent conversational E2E accuracy has been established.

## Preservation policy

- Keep the verified source snapshot on the **`v0.3.7.8-verified` branch**.
- Continue subsequent experimental work only on a separate branch such as `v0.3.0`. Do not modify `main` or the verified snapshot without explicit instruction.
- Keep existing Truth Gate semantics, raw corpus, model weights and provenance restrictions unchanged.
- Changes made after this checkpoint must be evaluated separately; this verification does not automatically apply to later commits.

Source of acceptance: local PowerShell console results supplied 2026-10-13.
