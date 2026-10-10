# LLM_CHA v0.2.33.7 — Content-Structure Binding

## Goal

Separate the problem of **knowing facts/content** from the problem of **expressing them in a requested structure**.

The same teacher response is used for a topic with two distinct input conditions:
- **Ungrounded**: just a direct question;
- **Grounded**: an explicit piece of information (definition or procedure steps) and an explicit output format.

Train an isolated response-only SFT checkpoint using disjoint training (CPU, GPU, Sensor; Photo Organization, Writing), validation (Microphone; Cleaning) and evaluation (Browser, Battery; Device Inspection) item groups. These topic splits reduce exact leakage but all examples are hand-designed, small, and share structure. Not a clean proof of general semantic internalization.

## PowerShell

```powershell
git fetch origin
git switch v0.2.33.7
git pull origin v0.2.33.7
python -m unittest -v test_content_structure_binding_v02337.py
python content_structure_binding_v02337.py train --epochs 25 --patience 5
python content_structure_binding_v02337.py evaluate
```

Expected checkpoints and reports:
- `model/model-llm-cha-content-structure-v02337.pt`
- `results/content_structure_train_v02337.json`
- `results/content_structure_eval_v02337.json`

## Interpretation

Compare generated answers in Grounded vs Ungrounded for the *same* unseen topic. Score whether the grounded facts were used and whether the requested sentence/procedure order was followed. A model may reproduce the required phrases without true generalized language generation, so perform human review. No DSS, Semantic Memory, or Bridge code is modified. Once the model can use supplied structured facts reliably, the next research step can feed those facts from **DSS / Semantic Memory** and optionally train a dedicated semantic Bridge against the improved foundation checkpoint.

A semantic condition provided externally is not internalized meaning recognition. The test uses only a few authored items and not an independent sealed benchmark. Retain old checkpoints; do not promote automatically.
