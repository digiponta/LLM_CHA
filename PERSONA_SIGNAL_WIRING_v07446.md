# v0.7.44.6 — Live Persona Audit + Low-Signal Reject

Observed runtime example: `ぬこ` produced a malformed sentence with
`min_tok_conf=0.064`, `agreement=0.020`, `persona_gap=true`,
yet passed the prior string-only gate.

The opt-in `LLM_CHA_RESPONSE_GATE=1` generation hook now evaluates the
actual `cha_persona_audit` on the *original generated response*. If
`primary.min_confidence < 0.10` or `agreement < 0.10`, it reports
`LOW_SIGNAL_REJECT`, emits a nonfactual fallback, and excludes that reply
from known history and learning. These thresholds are initial heuristics,
NOT calibrated error probabilities. Model outputs with normal signals and
persona gaps are labelled `PERSONA_GAP_OBSERVED`; this does NOT mean
persona quality has been resolved.

No rewriting of approved source evidence. No changes to Wikipedia,
Trusted retrieval, or Candidate fallback routes. No auto-promotion.
Bounded retry remains an isolated prototype, not wired to chat.py.

```powershell
git pull
python -m unittest -v test_response_quality_gate_v07443.py test_response_controller_v07444.py test_runtime_quality_wiring_v07445.py test_persona_signal_wiring_v07446.py
$env:LLM_CHA_RESPONSE_GATE="1"
python chat.py
Remove-Item Env:LLM_CHA_RESPONSE_GATE
```

Recommended manual probes: `猫`, `ぬこ`, `ネコ`, `ぬことは`,
`貴方の名前は`, `宇宙とは`. Inspect emitted `response_quality_gate`
and `train_ready` labels. A small sample is not comprehensive fluency
validation.
