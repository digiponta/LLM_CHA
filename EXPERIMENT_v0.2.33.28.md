# LLM_CHA v0.2.33.28 — Relative Position & Monotonic Pointer

## Background

v0.2.33.27 found that three Pointer head variants remain at **0/40 long-sequence exact copies** across all three stages. Teacher-forced long pointer-position accuracy rose from ~33–34% at Stage 1 to ~45–47% at Stages 2–3, while position accuracy deteriorated substantially after the first several copied tokens. Short-only and balanced validations both selected Stage 2.

## Goal

Determine whether giving the *pointer scoring function* an explicit relative progress bias or forward-moving constraint improves long-sequence copying without injecting any correct source position at inference time.

Four independently trained modes, identical frozen base and synthetic training schedules:

- **baseline**: Q/K-based Pointer with EOS logit (no position prior).
- **relative**: learned nonnegative penalty proportional to the distance between candidate source index and the number of output tokens already generated.
- **monotonic**: learned nonnegative penalty for candidate source indices lying *before* the previously **predicted** index during free generation.
- **combined**: both biases.

The source length is available from input. Output history length and the last predicted source index are observable at inference. Ground-truth pointer positions are used only as supervised training labels, never supplied as inference-time control.

Caution: the relative penalty uses an inductive bias that very closely matches the identity-copy task's output order. A gain would support an explicit *sequential copy mechanism*, not prove generic alignment learning applicable to arbitrary extraction or reordering. The monotonic training proxy approximates the previous index from output-history length; exposure-bias differences remain possible.

## Data / Selection

All arms share a three-stage schedule of 200 examples per stage:
- Stage 1 lengths 2–8
- Stages 2 and 3 lengths 2–18 (Stage 3 repeats Stage 2 examples)

Short and separate long validation sets contain 40 examples each. Save the checkpoint of minimum **balanced validation loss** (mean of short and long losses); do not select on test or novel-ID evaluation.

Tests: 40 each of short, long 12–18, unseen task IDs, mixed IDs, and extra novel IDs. Report exact autonomous copy including EOS, teacher-forced pointer-position accuracy and teacher-forced EOS selection. Main LanguageModel checkpoint, DSS, Semantic Memory, and Bridge are unchanged.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.28
git pull origin v0.2.33.28
python -m py_compile relative_monotonic_pointer_v023328.py
python -m unittest -v test_relative_monotonic_pointer_v023328.py
python relative_monotonic_pointer_v023328.py
```

Output:
- `results/relative_monotonic_pointer_v023328.json`
- Four heads in `model/relative_monotonic_pointer_v023328/`

Training includes four heads with multiple frozen backbone forwards per token; expect appreciable GPU runtime.

## Interpretation

If the relative branch improves long exact-copy results, the explicit sequential-position prior is helping. If only monotonic or combined improves, the constraint to follow previous predictions is beneficial. If training pointer accuracy improves but autonomous copying stays poor, inspect failure accumulation and EOS separately.

This is a **single-seed synthetic feasibility comparison** with different trainable-parameter counts, not a definitive attribution of performance to architecture. Further independent testing would be needed before any stable integration.
