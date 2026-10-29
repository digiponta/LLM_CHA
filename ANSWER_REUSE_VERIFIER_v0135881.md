# v0.13.58.81 — Conservative Answer Reuse Verifier

This *experimental* module adds a restricted ACCEPT path: normalized query must match the candidate question exactly, the answer must be nonempty, the request must not trip context/current-data/medical/action guards, and `source_id` must appear in an **independently audited** source approval file. Similarity, even 1.0, cannot itself authorize an answer.

AI-reviewed holdout labels are used only for post-hoc metrics and **must not** be copied into the approved-source list. Explicit approval is separate from factual truth; a source can be approved for provenance without every answer becoming correct. ACCEPT is a prototype policy decision, not a correctness guarantee.

Run:
```powershell
git fetch origin
git switch v0.13.58.81-conservative-reuse-verifier
python -m unittest -v test_answer_reuse_verifier_v0135881.py test_answer_reuse_verifier_v0135880.py
python answer_reuse_verifier_v0135881.py --input data/verifier_pairs_v0135881.csv --approved-sources data/independently_approved_sources.json --output results/answer_reuse_verifier_v0135881.json
```

Input requires `query,candidate_question,candidate_answer,score,source_id` (optional query_id,candidate_id,answer_reusable). Approval JSON schema: `{"approved_source_ids":["externally-audited-source-id"]}`. No approval file is provided automatically. The previous 1,344-row review CSV contains provisional AI review labels; it is not an approval file or sufficient basis for automatic acceptance.

No modifications to chat.py, weights, Semantic Memory or /sleep.
