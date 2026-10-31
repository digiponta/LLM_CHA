# v0.13.58.82.94 — Persona Pilot Quality Review

No new training. v0.93 found 2,286 unique CP-speaker response pairs across 157 train dialogues, from 2,313 target-speaker candidates (27 duplicates). Before training, verify persona suitability, data license, language and privacy.

Windows:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.94-persona-quality-review
python -m unittest -v test_real_persona_quality_v013588294.py test_real_persona_pilot_v013588293.py
python review_real_persona_quality_v013588294.py --source data-src/real-persona-chat --target-speaker CP --samples 12
```
The saved report only contains profile field **names/types**, count summaries and sampled fingerprints/lengths; it does not contain conversation text. For optional **local-only** content review use `--show-text`, and **do not upload unredacted output**. Review the source's license/terms and verify persona CP is appropriate; the tool does not attest to these or guarantee removal of personal information.

After reviewing CP, consider whether to train a general conversational adapter separate from Nagato persona. Export and train only with permission, explicit local review, heldout dialogue isolation and independent checkpoint paths. Avoid automatically treating a successful inventory as approval to publish or train.
