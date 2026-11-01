# LLM_CHA v0.13.58.83.15 — Semantic Memory state compatibility

Observed local execution v0.13.58.83.14: unified memory 57 rows, truth store 0 rows; query "閃亜鉛鉱とは" exactly matched unified:56 but falsely produced UNLEARNED due to new adapter's stricter approval criteria.

Repository inspection confirms the established `knowledge_state_resolver_v10100.py` has a UNIFIED lookup route and `knowledge_state_dispatcher_v10101.py` sends it to RETRIEVE; `truth_aware_dispatch_v10103.py` gives UNVERIFIED a WARN rather than treating it as absent. Thus presence and verified truth must be tracked separately.

This branch adds a **read-only diagnostic compatibility layer** which distinguishes:
- MEMORY_NOT_FOUND
- MEMORY_PRESENT_UNVERIFIED (existing answer preview, but not authorized for new RSE auto-adoption)
- MEMORY_VERIFIED_BY_TRUTH (explicit TRUE overlay; does not attest independent evidence quality)
- MEMORY_TRUTH_RESTRICTED
- MEMORY_AMBIGUOUS
- NON_CONCEPT

The exact query "閃亜鉛鉱とは" should now show MEMORY_PRESENT_UNVERIFIED rather than claim it is unlearned. The prior runtime may still retrieve it with a truth warning. The experimental RSE shadow does not adopt unverified memory or write to stores.

PowerShell:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.15-memory-state-compat
python -m unittest -v test_rse_memory_state_compat_v013588315.py test_rse_real_memory_readonly_v013588314.py
python rse_memory_state_compat_v013588315.py --query "閃亜鉛鉱とは"
python rse_memory_state_compat_v013588315.py --query "少しお話ししませんか？"
python rse_memory_state_compat_v013588315.py --query "今何してる？"
```

Limitations: this checks unified memory, not typed, canonical or internalized routes. The normal chat.py has additional precedence and is unaffected. No model changes, no truth state modification, no inference integration. The next step is comparison of true runtime routing and the shadow result before enabling any answer adoption.
