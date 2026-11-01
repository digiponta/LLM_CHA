# v0.13.58.83.09 — RSE Holdout Human Labeling

v0.13.58.83.08 sampled 30 CP answer pairs from 293 test-split candidates. They are dialogue-separated from the CP training subset, but all come from RealPersonaChat. No human labels have been verified.

This branch adds a **non-overwriting** review template and a label-completeness validator. It does not calculate gate accuracy before annotation. The test-split metadata file is immutable; the local review file is separate.

Windows PowerShell:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.09-rse-human-labeling
python -m unittest -v test_rse_human_review_v013588309.py test_rse_holdout_v013588308.py
python review_rse_holdout_v013588309.py --init
```

Review locally, without uploading private source dialogue text. The existing v0.13.58.83.08 tool's `--show-text` prints sampled question/answer pairs in stable order; match their IDs to the review template.

For **each** of the 30 cases, supply an independently phrased `new_query` and Boolean fields:
- `intent_match`: is the source question's intent consistent with the new query?
- `slot_match`: are required temporal, subject and requested-attribute slots compatible?
- `answer_suitable`: is the source answer appropriate for the independently phrased query?
- `persona_transfer_risk`: does reuse attribute a real participant's experiences to the AI?

Example value schema (do not automatically mark true):
```json
{
  "id": "FROM_HOLDOUT",
  "dialogue_id": "FROM_HOLDOUT",
  "new_query": null,
  "intent_match": null,
  "slot_match": null,
  "answer_suitable": null,
  "persona_transfer_risk": null,
  "reviewer_note": null
}
```

Save review decisions in `results/rse_human_review_v013588309.json`. Recheck:
```powershell
python review_rse_holdout_v013588309.py
```

The report will remain HUMAN_LABELING_PENDING until all cases have independently written queries and explicit labels. Completing this template alone does **not** independently validate human authorship, cross-dataset independence, Gate correctness or model generalization. Never use the test labels to tune the gate on the same set; use a development split for improvements.
