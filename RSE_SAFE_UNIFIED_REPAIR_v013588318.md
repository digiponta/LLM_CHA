# LLM_CHA v0.13.58.83.18 — Controlled Unified Memory Repair

The v0.13.58.83.17 diagnostics identified exactly one proposed fix in the local 57-row Unified store, row index 56 for concept 閃亜鉛鉱. Before/after:
- before: 閃亜鉛鉱は、亜鉛の硫化鉱物であるである。
- after: 閃亜鉛鉱は、亜鉛の硫化鉱物である。

This command defaults to a **dry run**, requiring the proposal to be regenerated if contents have changed. It accepts **exactly one change**; multiple unexpected repairs are refused. An explicit --apply and --approve-concept are mandatory for writing. It creates an immutable byte-for-byte backup adjacent to the store, atomically replaces the JSONL, and re-reads to confirm unchanged other records/metadata. The original atomic proposition store is never edited.

PowerShell:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.18-safe-unified-repair
python -m unittest -v test_rse_safe_unified_repair_v013588318.py test_rse_proposition_compose_fix_v013588317.py
python propose_rse_unified_repair_v013588317.py
python apply_rse_unified_repair_v013588318.py
```

Inspect output and verify it identifies exactly row_index=56, concept=閃亜鉛鉱, and the expected before/after.

**Apply intentionally, only after verifying the preview:**
```powershell
python apply_rse_unified_repair_v013588318.py --apply --approve-concept "閃亜鉛鉱"
python diagnose_rse_proposition_compose_v013588316.py --subject "閃亜鉛鉱"
python rse_memory_state_compat_v013588315.py --query "閃亜鉛鉱とは"
```

Expected: APPLIED_VERIFIED, a backup path, Unified answer without the doubled copula, other 56 rows logically unchanged. The RSE compatibility state remains MEMORY_PRESENT_UNVERIFIED until an explicit truth/approval provenance is present. Nothing changes chat.py or model weights.

Important: JSONL is re-serialized; other row objects are preserved but exact whitespace/formatting of other lines is not guaranteed. A backup is provided for byte-exact restoration. A post-write verification error preserves the backup and reports its location; manual recovery would then be necessary.
