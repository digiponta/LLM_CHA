# LLM_CHA v0.4.26 — Multi-Dimensional Response Quality Evaluation

This is a **human-only evaluation layer** on top of the v0.4.25 reviewed development samples. It does not generate ratings from LLM confidence/probe agreement, and does not alter the v0.4.22 binary benchmark, the Truth Gate, model weights, Semantic Memory, `/train` or `/sleep`.

## Human annotation contract

The four independent axes, each scored as `PASS`, `FAIL`, or `UNCERTAIN`:

- **relevance**: does the answer address the user's question? Required axis.
- **fluency**: is the text comprehensible, natural, and complete? Required axis.
- **persona_consistency**: is this an appropriate response for the configured character? Use `NOT_APPLICABLE` if character judgement is not meaningful.
- **grounding**: does the response correctly use available supporting facts/evidence? Use `NOT_APPLICABLE` if no factual grounding is needed; do not assume a reference is available.

The existing `gold_inappropriate` binary label is **not** automatically overwritten or derived from the axes. Disagreements are diagnostic evidence for human adjudication.

A dimensions JSONL record has **exactly** these keys:

```json
{"id":"capture-...","reviewer":"human-review","relevance":"PASS","fluency":"PASS","persona_consistency":"UNCERTAIN","grounding":"NOT_APPLICABLE"}
```

The record shown above is a schema illustration, **not** a judgment on any actual captured answer. The input is development-only. No independent holdout claims or auto-labeling.

## Windows verification

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_persona_quality_dimensions_v0426.py test_persona_quality_workflow_v0425.py test_persona_quality_capture_v0424.py test_persona_quality_annotation_v0423.py test_persona_quality_benchmark_v0422.py
python verify_integration_v0366.py --gpu --legacy --timeout 240

# First generate the human-review worklist without any dimensional annotations:
python persona_quality_dimensions_v0426.py --labeled results/persona_quality_labeled_v0425.jsonl --pending results/persona_dimensions_pending_v0426.jsonl --report results/persona_dimensions_report_v0426.json
Get-Content results/persona_dimensions_pending_v0426.jsonl -Encoding UTF8
```

After human review, write a separate `results/persona_dimensions_reviewed_v0426.jsonl` with one annotation record per reviewed ID, using the exact schema above. You may provide a partial set; remaining IDs stay pending. Run:

```powershell
python persona_quality_dimensions_v0426.py --labeled results/persona_quality_labeled_v0425.jsonl --dimensions results/persona_dimensions_reviewed_v0426.jsonl --pending results/persona_dimensions_pending_v0426.jsonl --report results/persona_dimensions_report_v0426.json
```

Interpretation: `axis_counts` counts only *actually human-reviewed* rows, and `binary_dimension_disagreements` identifies mismatches for additional human examination. Neither is an accuracy or independent-holdout statistic. Preserve privacy of the review files.
