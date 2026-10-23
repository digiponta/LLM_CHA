# LLM_CHA v0.7.24 — Experimental Adapter Restore

When both `LLM_CHA_MEMORY_FIRST=1` and
`LLM_CHA_MEMORY_FIRST_MODE=constrained` are set, `chat.py` now
tries to restore the latest valid `/sleep` Experimental Adapter from
`results/experimental_sleep_v0722/` on startup.

The restore validator requires that the checkpoint:
- is marked `route=experimental`, `approved=False`,
- has exactly the currently PENDING Candidate IDs,
- has a valid rank and adapter payload,
- is compatible with the loaded Base model and tokenizer.

A corrupt or stale checkpoint is skipped in favor of another valid
snapshot. Reloading does not change Trusted weights, Approved Semantic
Memory, or Candidate lifecycle states. Restored knowledge remains
`EXPERIMENTAL_UNVERIFIED`. For safety, the constrained generator's
response is not used as the final answer unless it matches the registered
Candidate exactly; Evidence is returned otherwise.

If no compatible sleep checkpoint exists, the existing constrained-mode
backend selection remains in place. This means the previously configured
synthetic experimental adapter could still be used; the code reports
`NO_CHECKPOINT` or `NO_VALID_CHECKPOINT` explicitly. Never interpret
such fallback as a successful restored model.

## Verification

```powershell
git fetch origin
git switch --track origin/v0.7.24
python -m unittest -v test_experimental_restore_v0724.py test_experimental_reload_v0723.py test_experimental_sleep_v0722.py
$env:LLM_CHA_MEMORY_FIRST="1"
$env:LLM_CHA_MEMORY_FIRST_MODE="constrained"
python chat.py
```

Expected startup diagnostic after a compatible prior sleep checkpoint:
`[experimental startup restore: status=RESTORED, ...]`.

The current tests verify routing and checkpoint structure with a fake
backend, not actual answer generalization or training retention. The
work on measured before/after generation quality and Trusted checkpoint
hash comparisons remains pending.
