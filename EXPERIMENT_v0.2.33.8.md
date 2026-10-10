# LLM_CHA v0.2.33.8 — Grounded Generation Diagnostics

## Objective

Identify the minimal input-to-output ability that is missing before further instruction fine-tuning or semantic bridge changes. **Evaluation only; absolutely no training or checkpoint mutation.** DSS, Semantic Memory and Semantic Bridge remain as they were.

The suite probes:

- **A Content Copy:** Can the LLM reproduce an explicitly supplied Japanese sentence?
- **B Content Extraction:** Can it select the relevant fact from multiple statements?
- **C Structure Transformation:** Can it turn a fact or ordered list into a specified Japanese sentence structure?
- **D Grounded Completion:** Can it finish a gold answer when provided the correct prefix?
- **E Negative/Counterfactual Grounding:** Does changing an invented fact's color from red to blue alter generation appropriately?

Compare the same 10 prompts between the original v0.2.21 base and trained v0.2.33.7 candidate. No external scoring model is used. Outputs have exact reference-text equality for diagnostic purposes and blank manual fidelity/fluency rating fields. Exact match is *not* a semantic metric for open-ended responses.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.8
git pull origin v0.2.33.8

python -m unittest -v test_grounded_generation_diagnostics_v02338.py
python grounded_generation_diagnostics_v02338.py
```

Outputs: `results/grounded_generation_diagnostics_v02338.json`.

The candidate model is `model/model-llm-cha-content-structure-v02337.pt` and must have been created by the prior experiment.

## Diagnostic decisions

- **Copy fails:** test tokenizer/decoder and copying training on varied novel strings, verify prompt format, and evaluate longer-context pass-through *before* assuming a sophisticated semantic deficit.
- **Copy passes but extraction fails:** train selection and relevance filtering separately.
- **Extraction passes but conversion fails:** focus on controlled restructuring of facts and answer formats.
- **Gold-prefix completion passes but free generation fails:** investigate answer initiation/decoding, separate teacher-forced NLL from true continuation.
- **Counterfactual variants produce the same answers:** weak conditioning / copying control, not proof of an absolute semantic inability.

These are few handcrafted prompts with no external benchmark. Assess manually; do not promote memory or assert internalized semantics based solely on this experiment.
