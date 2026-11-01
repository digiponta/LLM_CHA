# v0.13.58.83.07 — RSE ACCEPT_CANDIDATE development phase

This branch introduces a diagnostic ACCEPT_CANDIDATE classification for low-risk conversational exchanges such as greetings and invitations. Unlike REJECT or MANUAL_REVIEW_REQUIRED, this class is eligible for subsequent review and testing, **not automatic delivery**. The RealPersonaChat speaker's personal history must never become the assistant's claimed history.

The included 8 synthetic examples are development-only, NOT an independent human-labeled holdout. Reported precision and recall must not be treated as deployed performance. Other intents, including factual queries, still require separate Semantic Memory routing.

Windows PowerShell:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.07-rse-accept-candidates
python -m unittest -v test_rse_accept_candidate_v013588307.py test_rse_gate_benchmark_v013588306.py
python rse_accept_candidate_v013588307.py
```

Output: results/rse_accept_development_v013588307.json

Next: collect unseen human-judged positive and negative source question / answer matches, establish false-accept and coverage targets, inspect failures, and only then consider an isolated runtime shadow mode. Existing chat.py, Semantic Memory and all checkpoints are untouched.
