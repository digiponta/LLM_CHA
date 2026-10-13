# LLM_CHA v0.4.4 — Opt-in UNKNOWN Persona Literal Quote

The v0.4.3 real runtime trace established `文学`: dispatcher `UNKNOWN`, one matching source excerpt (line 410), no explicit Truth runtime BLOCK. `小説`: dispatcher `UNKNOWN`, zero corpus matches.

This optional rescue is **disabled by default**. When `LLM_CHA_UNKNOWN_PERSONA_QUOTE=1`, an UNKNOWN query matching an exact focus definition-request form can display the original persona excerpts as **related mentions, never verified definitions**. It does not change scientific Truth Gate records, model weights, source corpus, or the historical RAW_CORPUS_ONLY route. Explicit Truth Gate blocks and internalized-verification overrides retain priority; missing sources fall through to the existing UNKNOWN behavior. The response remains labeled `NOT_ASSESSED`.

## PowerShell validation

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_persona_unknown_quote_v0404.py test_persona_route_trace_v0403.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
$env:LLM_CHA_UNKNOWN_PERSONA_QUOTE="1"
$env:LLM_CHA_PERSONA_ROUTE_TRACE="1"
python chat.py
# ask: 文学とは / 小説とは /exit
```

Expected from earlier source diagnosis: literature emits a related-source quote only, while novel remains UNKNOWN. **This is a prediction, not yet a measured v0.4.4 runtime E2E result.** Verify the runtime log before claiming acceptance. The four MEANS_OF candidate verdicts are still UNREVIEWED, unrelated to this literal-quote facility.
