# v0.7.44.5 Opt-in raw-generation gate integration

After 15/15 isolated quality/controller tests passed, a narrowly-scoped guard
was added to `chat.py`. It applies only when `LLM_CHA_RESPONSE_GATE=1`,
`accepted=True`, and no Candidate fallback was selected. It checks the raw
model reply before display. A rejected reply becomes a fixed nonfactual
fallback and is excluded from accepted conversation history/training.

**This is NOT complete v0.7.44 integration**: the bounded retry controller,
persona_gap metadata, live adapter restoration and full Wikipedia/Trusted
regressions are not yet wired or exercised in the GPU runtime. The current
quality guard uses `persona_gap=False` because that signal is not present at
this generation site. It must not be represented as a persona-gap fix.

## PowerShell

```powershell
git pull
python -m unittest -v test_response_quality_gate_v07443.py test_response_controller_v07444.py test_runtime_quality_wiring_v07445.py
$env:LLM_CHA_RESPONSE_GATE="1"
python chat.py
Remove-Item Env:LLM_CHA_RESPONSE_GATE
```

Keep the environment flag disabled in production until the full GPU and
Trusted/Wikipedia regression suite has passed. No scientific truth is inferred
from Japanese response fluency.
