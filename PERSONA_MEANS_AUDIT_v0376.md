# LLM_CHA v0.3.7.6 — Persona Means Role Corpus Audit

This experimental stage adds a **read-only audit** of actual `data/data-nagato.txt` sentences. It records source line numbers, original text, subject, means, predicate, and means marker for narrowly recognized grammatical forms.

New recognized markers: `によって`, `を使って`, `を通じて`. The ambiguous particle `で` is **not** recognized automatically: it can encode location, manner, instrument, cause, etc.; expanding it first requires a disambiguation experiment. Only the existing v0.3.7.2 whitelist of `によって` predicates is permitted to produce a causative paraphrase; all other matches are *unrendered candidates*.

The audit **does not** auto-register these candidates with production Persona Memory, assign fact truth, alter existing retrieval order, or write to the source corpus. No actual corpus count has been measured until the script runs on the user's dataset. Future steps: assess extraction yield, rejected/false-positive cases, implement reviewed means-keyed lookups from extracted candidates, then broaden syntax conservatively.

## PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m unittest -v test_persona_means_audit_v0376.py test_persona_means_index_v0375.py
python persona_means_audit_v0376.py --report results/persona_means_audit_v0376.json
python verify_integration_v0366.py --gpu --legacy --timeout 240
```

Inspect `candidate_count`, `causative_derivable`, `unrendered_candidates` and `candidates` in the JSON report. Explicitly check whether a subject or means was captured with an unintended scope before using the results in an interactive persona answer.
