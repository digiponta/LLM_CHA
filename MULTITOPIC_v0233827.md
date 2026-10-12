# LLM_CHA v0.2.33.82.7 — Proposition-level Truth Overlay

Opt-in multi-topic runtime now assigns a deterministic proposition ID derived from
`(subject, exact proposition text, source provenance)`. Each proposition may
have a separate, **read-only, manually maintained** Truth State override.
Missing entries inherit the subject-level state. A FALSE/OUTDATED/CONTESTED
proposition is skipped, and an explicitly blocked subject cannot be unblocked
by a proposition-level TRUE record.

The overlay **never automatically verifies** scientific claims. No learning,
promotion, or memory writes are performed. Provenance is inherited from the
source unless an explicitly supplied overlay label is provided.

## Optional overlay JSONL

Set `LLM_CHA_PROPOSITION_TRUTH` to an existing JSONL file with records:
```json
{"proposition_id":"<24-hex-from-runtime-diagnostics>","truth_state":"FALSE","provenance":"manual-review:2026-10"}
```
Use actual IDs printed in `[proposition-id=...]` diagnostics. Do not
copy the placeholder string literally. Review decisions must be made by
a human/source-verification workflow; do not label a claim TRUE merely
because it appeared in a model's training corpus.

Without the environment variable, all propositions inherit the existing
subject Truth State (so current default behavior is preserved).

## Test and run
```powershell
git pull origin v0.2.33.82-multitopic-context
python -m unittest -v test_multi_topic_context_v0233821.py test_conversation_topic_adapter_v0233822.py test_multi_topic_chat_runtime_v0233823.py test_truth_aware_chat_integration_v0233824.py test_learning_init_v02338241.py test_grounded_followup_v0233825.py test_grounded_expansion_v0233826.py test_expansion_integration_v0233826.py test_proposition_truth_v0233827.py test_truth_integration_v0233827.py
$env:LLM_CHA_MULTITOPIC="1"
python chat.py
```
Expected **73 tests** (62 + 6 + 5), pending actual local verification.
Test initial/return/follow-up, blocked per-proposition overlays, all-blocked
fallback, subject FALSE, `/reset`, and unchanged behavior with flag off.
No GPU E2E results have yet been collected for this version.
