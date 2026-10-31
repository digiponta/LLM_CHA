# LLM_CHA v0.13.58.82.93 — RealPersonaChat Small Pilot

The v0.92 audit found 13,583 valid dialogues and 395,036 *candidate* adjacent opposite-speaker pairs, NOT 395k ready-to-train examples. This step **does not train a model**. A pilot requires explicit target speaker selection and review of the source's usage/license conditions.

## Windows: first a dry run (no text exported)

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.93-real-persona-pilot
python -m unittest -v test_real_persona_pilot_v013588293.py test_real_persona_pairs_v013588292.py

python prepare_real_persona_pilot_v013588293.py `
  --source data-src/real-persona-chat `
  --target-speaker CP `
  --max-pairs 5000
```

`CP` is **merely a frequent speaker ID in the audit**, not confirmed to be a suitable target persona. Replace it after inspecting `interlocutors.json` and reviewing speaker characteristics. The report `results/real_persona_pilot_v013588293.json` contains counts only. Target speaker IDs across the dataset are not interchangeable with persona "nagato".

Only **after verifying permission/licensing and reviewing the intended persona**, export with explicit flags:

```powershell
python prepare_real_persona_pilot_v013588293.py `
  --source data-src/real-persona-chat `
  --target-speaker CP `
  --max-pairs 5000 `
  --license-reviewed `
  --export
```

This creates `data/real_persona_pilot_v013588293.jsonl` (refuses to overwrite). Samples are sourced only from the stable *train* dialogue split. Simple email/phone/URL pattern filters and exact holdout prompt exclusion are included. These checks **do not establish semantic holdout independence**, consent, or absence of personal information. Manually inspect a representative sample locally, check licenses, and avoid uploading private dialogue data publicly.

**Before training:** Check data quality, whether the dialogue language matches the Japanese LLM, whether persona transfer is appropriate, and whether this pilot is large enough from one chosen speaker. Consider using dialogue training to improve general conversation only, separately from Nagato persona. For an eventual A/B train, create a new checkpoint and a new state; do not overwrite production.
