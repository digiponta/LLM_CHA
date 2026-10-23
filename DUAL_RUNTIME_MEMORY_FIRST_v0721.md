# LLM_CHA v0.7.21 — Optional Production Dual-LLM Memory-First Bridge

Integrates the v0.7.20 memory-first experimental path into existing
`chat.py`, while preserving its Trusted Semantic Memory, Truth Gate,
Wikipedia evidence, safe-greeting, and approved-answer precedence.

The new path only runs after an existing structured Trusted UNKNOWN:

- `UNKNOWN_KNOWLEDGE` (except Truth Block/internalized stale), or
- `GATE_REVIEW` with low response agreement, no context recovery,
  and no internalized record.

Opt in explicitly with `LLM_CHA_MEMORY_FIRST=1`. In `evidence` mode
(default), retrieve Candidate Semantic Memory without loading Experimental
weights. In `constrained` mode, load the Experimental Adapter lazily,
pass retrieved Candidate evidence into its prompt, compare the generated
answer against the Candidate answer, and reject inconsistent generation
while preserving unverified evidence. Both retain Candidate ID and source ID
internally; the answer is visibly labeled `未承認・候補知識`. No Trusted
memory writes, automatic promotion, or weight changes occur.

**Important limitation:** Candidate retrieval is lexical, may make an
incorrect match, and can give false positives. An unverified candidate
is never evidence of objective factual truth. The legacy
`LLM_CHA_EXPERIMENTAL_FALLBACK` route remains unchanged when Memory-First
is disabled. The production bridge currently points at
`data/candidates_v071.jsonl` and `data/approved_v071.jsonl`, not the
isolated four-fact dataset unless you explicitly copy/test in a separate
environment. Do not copy synthetic evaluation facts to real Approved Memory.

## Windows

```powershell
git fetch origin
git switch --track origin/v0.7.21
python -m unittest -v test_dual_runtime_bridge_v0721.py test_experimental_memory_first_v0720.py
$env:LLM_CHA_MEMORY_FIRST="1"
$env:LLM_CHA_MEMORY_FIRST_MODE="evidence"
python chat.py
Remove-Item Env:\LLM_CHA_MEMORY_FIRST
Remove-Item Env:\LLM_CHA_MEMORY_FIRST_MODE
```

Optional generation comparison:
```powershell
$env:LLM_CHA_MEMORY_FIRST="1"
$env:LLM_CHA_MEMORY_FIRST_MODE="constrained"
python chat.py
```
Constrained mode uses an Experimental Adapter checkpoint from
`results/multi_fact_v0715/experimental-adapter.pt`; it was trained on the
synthetic four-fact fixture, **not** necessarily the Candidate entries in
the production store. Use evidence mode for initial integration verification.

Do not interpret a passing unit test as measured end-to-end Trusted
knowledge retention. This branch still needs runtime tests and audit of
false Candidate retrieval under more varied Japanese questions.
