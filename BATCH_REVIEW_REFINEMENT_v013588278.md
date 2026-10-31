# v0.13.58.82.78 — Empty Batch and Re-review Proposal

Changes:
- `batch_semantic_approval_v013588277.py approve` now prints `EMPTY_BATCH_SKIPPED` without prompting when there are no eligible items. This is a normal no-op, not an approval or a commit.
- `sense_rereview_proposals_v013588278.py` records separate source-bound proposals for conditional/deferred AI decisions. It **never** mutates the original AI decision, human approval state, or any Semantic Memory. Promoting a recommendation requires independent evidence and a separately reviewed acceptance workflow in a later release.
- For the current frozen four candidates, there are zero eligible items: the sphalerite sense has already been registered; the other three are still deferred/conditional. Do not bypass that outcome.

Windows:

    cd C:\Users\inoma\git\misc\LLM_CHA
    git fetch origin
    git switch v0.13.58.82.78-batch-review-refinement
    python -m unittest -v test_sense_rereview_v013588278.py test_batch_semantic_approval_v013588277.py
    python batch_semantic_approval_v013588277.py prepare @batch
    python batch_semantic_approval_v013588277.py approve @batch

The last command should exit normally with `EMPTY_BATCH_SKIPPED` and not request yes/no for this dataset.

To record a re-review proposal, create a JSON dictionary keyed by actual candidate ID containing a `decision` (DEFER, RECOMMEND_APPROVE_WITH_CAUTION or RECOMMEND_APPROVE) and a justified `note` after independently checking the source. Then use:

    python sense_rereview_proposals_v013588278.py --decisions data/sense_rereview_decisions.json

Do not treat the proposal as accepted or ready for import. The currently implemented workflow cannot automatically change its authoritative review.
