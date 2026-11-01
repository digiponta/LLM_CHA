# LLM_CHA v0.13.58.83.13 — Verified Memory → Theme RSE Shadow Adapter

Read-only architectural experiment; DOES NOT connect to the real Semantic Memory store or chat.py.

Priority:
1. Exact query match in explicitly approved AND verified synthetic memory records.
2. Otherwise use the v0.13.58.83.12 theme/intent/relation selector.
3. If no uniquely supported safe response exists, return status UNLEARNED and exactly "未学習です".

Unverified facts are never promoted. Theme examples are synthetic and not evidence of generalized semantic reasoning. The sample claim about sphalerite is only a demonstration input; this adapter does not confirm provenance by itself.

PowerShell:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.13-memory-theme-shadow
python -m unittest -v test_rse_memory_theme_shadow_v013588313.py test_rse_semantic_theme_v013588312.py
python rse_memory_theme_shadow_v013588313.py --query "スファレライトの化学組成は？"
python rse_memory_theme_shadow_v013588313.py --query "少しお話ししませんか？"
python rse_memory_theme_shadow_v013588313.py --query "今何してる？"
```

Expected: MEMORY_SELECTED, ANSWER_SELECTED, UNLEARNED, respectively.

Next connect a true read-only adapter to existing Semantic Memory approved records, preserving provenance and the factual-answer route; evaluate independently before GUI/chat integration. No live model generation and no changes to chat.py.
