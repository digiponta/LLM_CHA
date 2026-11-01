# LLM_CHA v0.13.58.83.17 — Proposition Copula Fix and Repair Preview

Diagnosis v0.13.58.83.16 confirmed atomic value `亜鉛の硫化鉱物である` and the resulting duplicated string `閃亜鉛鉱は、亜鉛の硫化鉱物であるである。` at atomic composition and Unified Memory. `compose_propositions()` now removes terminal copulas from *values during rendering only*, leaving atomic records untouched; handles multiple values and de-duplicates mixed already-suffixed/unsuffixed values.

A separate `propose_rse_unified_repair_v013588317.py` reads the atomic and Unified stores, constructs atomic-backed repair proposals only for stored answers that contain the duplicate "であるである", and writes to `results/` only. **It does not edit the Unified file, or auto-authorize changes.** Review each proposed change before adding an explicit approved migration in a subsequent branch.

Windows PowerShell:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.17-proposition-compose-fix
python -m unittest -v test_rse_proposition_compose_fix_v013588317.py test_rse_proposition_compose_v013588316.py
python diagnose_rse_proposition_compose_v013588316.py --subject "閃亜鉛鉱"
python propose_rse_unified_repair_v013588317.py
```

The updated composer should no longer generate duplicated "である" from a value already ending in "である", but existing Unified records remain unchanged until explicitly migrated. The reported `atomic_compose` should be fixed; `unified_answers` may still show the old duplicate.

No training or chat.py changes. Check source-specific regression tests and inspect proposals before any data writes.
