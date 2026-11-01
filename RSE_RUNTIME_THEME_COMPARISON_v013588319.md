# v0.13.58.83.19 — Legacy Unified vs Theme RSE component comparison

v0.13.58.83.18 successfully repaired the local Unified record for 閃亜鉛鉱, leaving 57 records and a backup. This version compares the existing `knowledge_state_resolver_v10100.unified_lookup_row()` component with the experimental Theme RSE shadow on the same local store, without changing `chat.py`.

This is NOT a full live `chat.py` execution. The full runtime has additional TYPED, CANONICAL, Truth-Aware, Topic Context and other routing paths not invoked by this script. An existing UNIFIED answer appears as a **preview** in shadow (not an approved production response).

Windows:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.19-runtime-theme-comparison
python -m unittest -v test_rse_runtime_theme_comparison_v013588319.py test_rse_memory_state_compat_v013588315.py
python compare_rse_runtime_theme_v013588319.py `
  --query "閃亜鉛鉱とは" `
  --query "少しお話ししませんか？" `
  --query "今何してる？"
```

Detailed report: `results/rse_runtime_theme_comparison_v013588319.json`.
Expected categories: preserved Unified answer preview, theme-selected invitation, and UNLEARNED for unmatched activity. These outcomes are component comparisons, not measured live-conversation regressions. Existing chat.py, memory stores and checkpoint weights are untouched. Next: capture actual legacy runtime outputs in a separate read-only harness and compare against shadow before any integration.
