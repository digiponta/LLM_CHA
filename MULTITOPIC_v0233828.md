# LLM_CHA v0.2.33.82.8 — Human Review & Mixed Truth State

Adds a **separate administrator-operated review CLI**. It writes only an
explicitly designated proposition-truth JSONL overlay; it does not edit
Semantic Memory, the subject-level Truth Store, conversation state, or model.

## Review requirements

A user/reviewer must supply the exact proposition ID printed by the runtime,
an explicit Truth State, evidence reference, reviewer, and reason. The CLI
does not verify the cited evidence. TRUE is therefore a manual assertion,
not an automated scientific verification.

Conflicting changes (e.g. FALSE -> TRUE) are rejected rather than silently
overwriting an earlier review. Review the evidence and resolve conflicts
under a future audited revision workflow.

The runtime already reads an optional overlay at startup using
`LLM_CHA_PROPOSITION_TRUTH`. After editing the review file, restart chat.
The subject-level Truth Gate remains authoritative: TRUE cannot override a
blocked FALSE/OUTDATED/CONTESTED subject.

## Commands

```powershell
git pull origin v0.2.33.82-multitopic-context

python -m unittest -v test_multi_topic_context_v0233821.py test_conversation_topic_adapter_v0233822.py test_multi_topic_chat_runtime_v0233823.py test_truth_aware_chat_integration_v0233824.py test_learning_init_v02338241.py test_grounded_followup_v0233825.py test_grounded_expansion_v0233826.py test_expansion_integration_v0233826.py test_proposition_truth_v0233827.py test_truth_integration_v0233827.py test_proposition_review_v0233828.py
```

Expected count: **82 tests (73 + 9)**, pending local verification.

The example IDs below are from the actual previous runtime diagnostic log:
- `3be067eb21df502384387355` (first 宇宙 proposition)
- `86aca80929965d376a8ee66b` (second 宇宙 proposition)
- `745b400db9b193c610d29d51` (third 宇宙 proposition)

**Do not label these TRUE or FALSE without independently checking the
specific claim.** For a controlled mixed-state experiment, use a separate
test dataset and ids created by the test fixture; do not change the real
corpus review status merely to force a test outcome.

Example to record a genuine completed review (replace all placeholders):
```powershell
python proposition_review_v0233828.py --file data/proposition_truth_review.jsonl --id ACTUAL_24_HEX_ID --state UNVERIFIED --evidence "source:pending-check" --reviewer "reviewer-id" --reason "Awaiting independent verification"
$env:LLM_CHA_PROPOSITION_TRUTH="data/proposition_truth_review.jsonl"
$env:LLM_CHA_MULTITOPIC="1"
python chat.py
```

## Limits

The test suite covers mixed-state decisions against an in-memory fixture
and review JSONL handling; it does not prove real-world factual correctness,
live GPU filtering, or comprehensive tamper-resistant audit history.
File updates are atomic but not synchronized across multiple writers.
Concurrent administrative reviewers require a dedicated locked/audited store.
