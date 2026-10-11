# LLM_CHA v0.2.33.64 — Semantic Memory Coverage & Evidence Admission Diagnostics

Read-only `/refcoverage` command joins **Atomic Propositions**, **Subject Index**, **Typed Index**, **Unified Semantic Memory** and **Subject-Keyed Corpus Memory** (JSONL), plus the effective knowledge-resolution result for the mapped concept. An existing evidence manifest is reported as present/absent without assigning it truth.

The command requires the opt-in `--session-reference-memory`, approved session reference, and approved concept mapping. It reports per-layer counts, derived-only orphans, `Knowledge`, `Truth`, and the reason `evidence_gate()` refuses or considers metadata admissible.

**Important**: This command does not migrate raw corpus into atomic propositions, does not write to any layer, and does not certify `TRUE`. `eligible_by_metadata` is not independent verification. The corpus-memory counter matches exact `subject` or `concept` JSON fields, not arbitrary text mentions or raw `data-nagato.txt` occurrences.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.64
git pull origin v0.2.33.64
python -m py_compile chat.py semantic_coverage_admission_v023364.py
python -m unittest -v test_semantic_coverage_admission_v023364.py test_multilayer_semantic_audit_v023363.py
python chat.py --session-reference-memory
```

After existing `cursor → 量子力学` approval, run `/refaudit`, `/refcoverage`, `/refchain 量子力学はCを含む`. No evidence manifest means `/refchain` remains fail-closed with `no_evidence_manifest`.

The new tests cover raw corpus presence with no atomic propositions, UNVERIFIED admission rejection, unified presence not establishing truth, missing manifest, missing corpus file. Tests use temporary paths.
