# v0.2.33.4 — Language Generation Capability Baseline

## Purpose

Before changing the Semantic Memory or Semantic-to-Generation Bridge, directly inspect the pretrained LLM_CHA's ability to produce coherent Japanese. The architecture is kept unchanged and **the DSS, Semantic Memory, Bridge, and all checkpoints remain intact**.

We evaluate the **frozen base** in six categories: A text continuation, B definition/explanation, C ordered procedure, D multi-turn context reference, E task-specific conditional response, R retention of known small-chat behavior.

No semantic labels, teacher vectors, staged curriculum, or contrastive loss are used for this evaluation. There is **no training**.

## Windows commands

```powershell
git fetch origin
git switch v0.2.33.4
git pull origin v0.2.33.4
python -m unittest -v test_language_generation_baseline_v02334.py
python evaluate_language_generation_baseline_v02334.py
```

Optional trained checkpoint comparison, for exploratory reference:

```powershell
python evaluate_language_generation_baseline_v02334.py `
  --compare model/model-llm-cha-curriculum-staged-v02331.pt `
  --out results/language_generation_compare_v02334.json
```

Reports include each prompt, response, expectation and **unfilled manual human review fields** (fluency, task_success, factuality, notes). Output cannot be overwritten without choosing a fresh report path.

## Interpretation

- Weak A, B, C → optimize foundation pretraining and language-generation SFT before investing further in Bridge.
- A, B, C strong but D, E weak → focus on dialogue/reference and instruction following.
- A–E strong but purpose-transfer weak → revisit meaning-specific supervision and bridge design.
- The prompts are a *small exploratory diagnostic set*, not a statistically robust benchmark or an untouched future test. Manual ratings are necessary. Even an improvement would not prove autonomous DSS-free semantic internalization.

Avoid automatically promoting memory based on this experiment. Legacy `chat.py` or DSS-specific outputs are not substituted for native model output.
