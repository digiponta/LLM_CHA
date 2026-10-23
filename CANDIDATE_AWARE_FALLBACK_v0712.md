# LLM_CHA v0.7.12 — Candidate-Aware GATE_REVIEW Fallback

Adds an explicitly opt-in fallback from the **rejected-generation gate** in
production `chat.py`, in addition to v0.7.11's structured
`UNKNOWN_KNOWLEDGE` path.

## Route policy

The new fallback is attempted only if:
- `LLM_CHA_EXPERIMENTAL_FALLBACK=1`
- The Trusted generated response was **not accepted**.
- The observed gate reason is `low response agreement` (current narrow
  representation of the tested GATE_REVIEW case).
- No trusted context recovery or internalized evidence bypasses the gate.
- Exactly one **PENDING** Candidate Memory record has the same exact question.
- The Experimental result passes the v0.7.11 heuristic response gate.

Neither mere UNKNOWN text nor arbitrary rejected outputs cause fallback.
Experimental replies are labeled as `EXPERIMENTAL_UNVERIFIED`;
no automatic promotion, model training, or trusted history recording is
authorized by this fallback.

## PowerShell

```powershell
git fetch origin
git switch --track origin/v0.7.12
python -m unittest -v test_candidate_aware_fallback_v0712.py test_experimental_quality_v0711.py
$env:LLM_CHA_EXPERIMENTAL_FALLBACK="1"
python chat.py
Remove-Item Env:\LLM_CHA_EXPERIMENTAL_FALLBACK
```

Try the previously registered PENDING question
`v072実験の合言葉は何ですか`. If it again enters the low-agreement
GATE_REVIEW path, the Candidate-aware fallback is eligible. An answer
containing the v0.7.11 forbidden experimental training phrase will
be rejected, preserving the Trusted UNKNOWN display.

## Limitations

This version specifically targets the observed low-response-agreement
GATE_REVIEW case rather than every possible UNKNOWN route. Exact-match
Candidate lookup may miss paraphrases. The heuristic response gate cannot
verify factual correctness. This code does not unify all Truth Gate states
or replace the existing Wikipedia, Semantic Memory, and safe-greeting routes.
