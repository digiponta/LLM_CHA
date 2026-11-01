# v0.13.58.83.22 — Approved RSE Candidate Lifecycle

Explicit, local approval is required before an RSE answer can be adopted by the independent policy. This is **not wired to chat.py** and never writes model weights or Semantic Memory. Approval is evidence of operator acceptance of a response candidate, **not** a claim that external facts have been verified. Each candidate retains its source, query, answer, theme, intent, time slot, content fingerprint, state and reviewer.

States: PENDING -> APPROVED -> REVOKED (revoked IDs cannot be silently reused). A changed question/answer after approval invalidates its fingerprint and is excluded from selection.

Windows:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.22-approved-rse-lifecycle
python -m unittest -v test_rse_candidate_lifecycle_v013588322.py test_rse_adoption_policy_v013588321.py
python rse_candidate_lifecycle_v013588322.py register --id conversation_invite_v1 --question "少しお話ししませんか？" --answer "もちろん。何について話しましょう？" --source "manual-curation"
python rse_candidate_lifecycle_v013588322.py resolve --query "少しお話ししませんか？"
```

Review the registered candidate's exact text and context yourself before authorizing:
```powershell
python rse_candidate_lifecycle_v013588322.py approve --id conversation_invite_v1 --reviewer local-human
python rse_candidate_lifecycle_v013588322.py resolve --query "少しお話ししませんか？"
python rse_candidate_lifecycle_v013588322.py resolve --query "今何してる？"
python rse_candidate_lifecycle_v013588322.py revoke --id conversation_invite_v1 --reviewer local-human
```

Expected: before approval ABSTAIN, after approval SELECT_RSE for invitation, still ABSTAIN for unrelated current activity, after revocation ABSTAIN again. Existing protected route takes precedence.

Note: register/approve/revoke are **explicit filesystem writes** to `data/rse_candidate_lifecycle_v013588322.json`, separate from Semantic Memory. The evaluator `resolve` reads only. This initial schema is for single-user local research; it lacks independent authorization, cryptographic signature/HMAC, audit log and multi-process locking. Do not treat the reviewer string as identity authentication. Do not yet auto-approve examples or deploy as a production policy.
