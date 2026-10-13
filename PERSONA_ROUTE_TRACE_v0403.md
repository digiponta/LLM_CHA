# v0.4.3 Persona Route Trace (diagnostic-only)

v0.4.2 established that the persona corpus contains **文学** (one literal segment) but not **小説** (zero). The previous interactive transcript returned UNKNOWN for both. Source evidence alone does not establish that the full runtime invokes the Persona rescue.

In `chat.py`, the existing source-only rescue requires `dispatch.action == "BLOCK"` **and** `dispatch.state == "RAW_CORPUS_ONLY"`. When state is `UNKNOWN`, it is not entered, even if `ranked_persona_reply` finds source excerpts. Other guards include truth runtime BLOCK and internalized-verification overrides.

Set `LLM_CHA_PERSONA_ROUTE_TRACE=1` to print a read-only JSON trace after semantic dispatch and verification-override resolution. The trace includes the actual action, state, focus, truth runtime status, source excerpt count, the rescue eligibility predicate, and reasons if ineligible. `persona_rescue_hit_possible` means only that this branch could use a source excerpt, **not** that it has done so, or that the excerpt is a factual definition. Runtime routing and Truth Gate are unchanged.

## PowerShell

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_persona_route_trace_v0403.py test_persona_concept_coverage_v0402.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
$env:LLM_CHA_PERSONA_ROUTE_TRACE="1"
python chat.py
# Ask: 数学とは / 量子力学とは / 文学とは / 小説とは /exit
```

Share the `[persona-route-trace=...]` lines and final responses. Do not interpret literal occurrence, including `数学は、文学の分類`, as a verified definition of literature. No model retraining or corpus mutation is performed.
