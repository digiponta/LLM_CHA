# LLM_CHA v0.7.37 — Reference-based Candidate Auto-Approval

A PENDING Candidate is automatically promoted to the Approved JSONL store
after it is actually returned by the Experimental Memory-First route
**more than** a configured threshold number of times (default = 10).
For the default setting, the **11th reference** triggers approval.

Rules:
- Count an actual unique runtime response event from
  `EXPERIMENTAL_MEMORY_FIRST` (the same user question repeated in separate
  turns counts each time).
- No count for Wikipedia-only, RAW_CONCEPT_EVIDENCE, CORPUS_MEMORY,
  Trusted/identity responses, or candidates with no lexical MATCH.
- Count is persisted with `reference_count` and `reference_version`
  in `data/candidates_v071.jsonl`; restart does not reset it.
- The version is hashed from question, answer, and source ID. A
  modification restarts the count at one.
- At count 11, `DualMemory.approve` promotes into
  `data/approved_v071.jsonl` and removes the PENDING entry. Conflicts
  with an existing Approved answer block promotion.
- At the next exact question after approval, the bridge returns the
  Approved answer without calling the Experimental adapter.
- The result continues to preserve source metadata; reference frequency
  alone does **not** establish scientific factual correctness.
- The Experimental Adapter checkpoint may require regeneration to match
  the smaller remaining PENDING Candidate set at next startup.

## PowerShell

```powershell
git fetch origin
git switch --track origin/v0.7.37
python -m unittest -v test_reference_approval_v0737.py
$env:LLM_CHA_MEMORY_FIRST="1"
$env:LLM_CHA_MEMORY_FIRST_MODE="constrained"
$env:LLM_CHA_AUTO_APPROVE_REFERENCES="10"
python chat_window_v061.py
```

New diagnostic:
`[candidate_reference: status=COUNTED, count=10, threshold=10, promoted=False]`
and on the 11th reference:
`[candidate_reference: status=AUTO_APPROVED, count=11, threshold=10, promoted=True]`.

NOTE: auto-approval is enabled by the current v0.7.37 runtime with
default threshold 10. For a stricter policy, set a higher threshold.
This scheme measures stability and usage, not verification against
external facts. Concurrent independent chat processes are not supported
for reference count updates; run only one writer.
