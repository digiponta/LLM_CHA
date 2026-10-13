# LLM_CHA v0.4.25 — Incremental Human Annotation Workflow

The workflow combines v0.4.24 opt-in captured real answers, historical human-reviewed development labels and fresh manual annotations, while producing a pending-only review queue. It does not run inference, train the model, update Semantic Memory, or affect Truth Gate.

## Behavior

- Requires unique capture IDs and unique exact trimmed question–answer pairs. Duplicate pairs fail closed to prevent accidentally double-counting repeated runs; clean the source ledger first.
- Reuses human-reviewed `development` labels by stable ID only when **all** captured fields still match exactly.
- Raises an error if an answer or diagnostic score changed after review, if a reviewed ID is missing, or if two human labels conflict.
- New annotations must be explicit `{"id":"...","gold_inappropriate":false,"reviewer":"..."}`; labels are never guessed.
- Writes only unanswered review items to `--pending`, and accumulated development labels to `--labeled`.
- Evaluation reports are **development-only**, with no independent-holdout accuracy claim.
- The pending file is a human-readable queue, **not** a valid labeled benchmark input.

## Windows commands

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_persona_quality_workflow_v0425.py test_persona_quality_capture_v0424.py test_persona_quality_annotation_v0423.py test_persona_quality_benchmark_v0422.py
python verify_integration_v0366.py --gpu --legacy --timeout 240

# First reconcile existing human labels with recorded runtime answers:
python persona_quality_workflow_v0425.py --captures results/persona_capture_new.jsonl --prior results/persona_quality_labeled_v0423.jsonl --pending results/persona_quality_pending_review_v0425.jsonl --labeled results/persona_quality_labeled_v0425.jsonl
```

Review `results/persona_quality_pending_review_v0425.jsonl` and create a **separate** JSONL of new annotations with ID, human-approved boolean gold label, and reviewer string. For example, each line must be one JSON object; do not use the pending file itself as annotations.

```powershell
python persona_quality_workflow_v0425.py --captures results/persona_capture_new.jsonl --prior results/persona_quality_labeled_v0423.jsonl --annotations results/persona_annotations_new_v0425.jsonl --pending results/persona_quality_pending_review_v0425.jsonl --labeled results/persona_quality_labeled_v0425.jsonl
```

The previously reviewed v0.4.23 file contains the two original captures; the two newer captures should remain pending until a human labels them. After a subsequent run, pass the latest `results/persona_quality_labeled_v0425.jsonl` as `--prior` and **do not simultaneously pass an outdated conflicting label set**.

Because the user has seen example questions/responses during development, these are **not an independent sealed holdout**. A separate sampling and blinded-review protocol is required before publishing generalization metrics. All captures may contain sensitive user dialogue; do not commit raw captures to GitHub without reviewing them.
