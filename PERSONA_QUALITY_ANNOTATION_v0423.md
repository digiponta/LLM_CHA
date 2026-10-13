# LLM_CHA v0.4.23 — Independent Quality Dataset Preparation and Human Annotation

The v0.4.22 benchmark is functional, but its two existing development examples do **not** measure generalization. v0.4.23 adds an annotation preparation pipeline, not new fabricated gold data or new model inference. This version leaves chat.py, model training, semantic memory, Wikipedia and Truth Gate untouched.

## Protocol

1. On a fixed model/checkpoint, capture new real `question`/`answer` pairs with the **observed** `agreement`, `semantic_agreement`, and `runtime_accepted` signals into UTF-8 JSONL. Each capture must have an independent unique ID.
2. Exclude historical/development questions and any duplicates before annotation. The CLI has a minimum predefined exclusion list drawn from prior experiments; maintain a full frozen exclusion ledger when collecting a larger sample.
3. Freeze captures and version/hash the dataset. The generated `dataset_sha256` is a content checksum for reproducibility, **not proof of independence**.
4. Human annotators label answer appropriateness **without seeing model warnings**. Their labels are recorded separately as `id`, `gold_inappropriate` (true/false), `reviewer`. Resolve ambiguous labels according to a prespecified rubric; if undecidable, do not force it into a binary label.
5. Export the complete labeled dataset only after all reviewed IDs match. Use development for design work. Holdout should be sealed and created independently with documented sampling/provenance; the script cannot attest to holdout independence.
6. Use `persona_quality_benchmark_v0422.py` to score the frozen warning policy. Publish n, TP, FP, TN, FN, precision, recall, FPR, FNR and per-intent breakdown separately. Do **not** tune thresholds on a holdout.

## Capture schema example (illustrative metadata only — no actual captured observations supplied)

```json
{"id":"new-run-0001","question":"（新しい実入力）","answer":"（実際の応答）","agreement":0.5,"semantic_agreement":0.5,"runtime_accepted":true}
```

These numeric values are placeholders only. Replace them with instrumented values from real runtime runs; never treat the example as an evaluation sample.

## Human annotation schema

```json
{"id":"new-run-0001","gold_inappropriate":false,"reviewer":"reviewer-1"}
```

This is a schema demonstration, not a human judgment.

## Usage

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.4.0
git pull --ff-only origin v0.4.0

python -m unittest -v test_persona_quality_annotation_v0423.py test_persona_quality_benchmark_v0422.py test_persona_response_shadow_v0421.py
python verify_integration_v0366.py --gpu --legacy --timeout 240

# After preparing real captures in results/persona_capture_new.jsonl:
python persona_quality_annotation_v0423.py --captures results/persona_capture_new.jsonl --prepared results/persona_quality_pending_v0423.json

# After separate blinded annotation into results/persona_human_annotations.jsonl:
python persona_quality_annotation_v0423.py --captures results/persona_capture_new.jsonl --prepared results/persona_quality_pending_v0423.json --annotations results/persona_human_annotations.jsonl --labeled results/persona_quality_labeled_v0423.jsonl --split development

python persona_quality_benchmark_v0422.py --dataset results/persona_quality_labeled_v0423.jsonl --split development
```

**Known limitations:** the pipeline requires manually captured real model output and annotation; it does not yet extract telemetry from `chat.py` automatically, calculate inter-annotator agreement, guarantee disjoint paraphrase families, or certify an independent holdout. The user must supply genuinely new data and labels. Do not report independent quality scores before these steps.
