# v0.13.58.83.16 — Atomic proposition to Unified Memory diagnosis

Observed v0.13.58.83.15: unified:56 has "閃亜鉛鉱は、亜鉛の硫化鉱物であるである。". Root cause is not yet proven from the saved logs. Source inspection indicates compose_propositions / compose_typed_rows append "である。" unconditionally, so a stored value already ending "である" could cause the duplicated phrase.

This release examines four **actual local stores** without updating them:
atomic data/semantic_propositions_v1090.jsonl;
subject index data/subject_keyed_propositions_v1090.jsonl;
typed index data/typed_subject_propositions_v10100.jsonl;
unified data/unified_semantic_memory_v1090.jsonl.

Windows PowerShell:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.16-proposition-compose-diagnostic
python -m unittest -v test_rse_proposition_compose_v013588316.py test_rse_memory_state_compat_v013588315.py
python diagnose_rse_proposition_compose_v013588316.py --subject "閃亜鉛鉱"
```

Report: results/rse_proposition_compose_diagnostic_v013588316.json. Review atomic_values, atomic_compose, subject_index_values, typed_values and unified_answers, and the duplicated_at flags. Do not run a migration or rewrite any stored value until the origin is identified. The files are accessed read-only; the script only writes its separate diagnostic report.
