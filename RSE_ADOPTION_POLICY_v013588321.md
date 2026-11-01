# v0.13.58.83.21 — Theme RSE Answer Adoption Policy (Shadow)

Observed actual chat.py responses in v0.13.58.83.20:
- 閃亜鉛鉱とは -> correct result via MEMORY_ATOMIC_EXACT
- 少しお話ししませんか？ -> 「無用。お疲れさまでした。」, despite gate=KNOWN
- 今何してる？ -> 「少しだけはとりやすい。」, despite gate=KNOWN

This branch adds an **independent**, read-only decision policy and tests. No change to chat.py, model, or semantic stores.

Policy:
1. Preserve existing answer when an explicitly protected existing knowledge route (e.g. MEMORY_ATOMIC_EXACT) is observed.
2. If Theme RSE finds a candidate, require **explicit approval** before adoption. Synthetic example candidate is not automatically approved.
3. If no appropriate candidate is available, abstain with 「未学習です」, ignoring model confidence/KNOWN as evidence of relevance.
4. Ambiguous, unverified or truth-restricted memory requires review or established existing trust policy. Do not mark unverified memory verified.

Windows:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.21-rse-adoption-policy
python -m unittest -v test_rse_adoption_policy_v013588321.py test_rse_live_transcript_v013588320.py
python evaluate_rse_adoption_policy_v013588321.py
```

Detailed report: `results/rse_adoption_policy_v013588321.json`.
Expected policy results for the three captured cases: PRESERVE_EXISTING, REVIEW_REQUIRED, ABSTAIN. Thus the correct conversational candidate is **not yet adopted**, pending a real approval mechanism. The next step is to link to existing approved-candidate lifecycle and then compare behavior in an isolated opt-in runtime. NOTE: policy decisions from historical transcript logs are simulated; this is not live interception.
