# LLM_CHA v0.2.33.40 — Clarification Interruption & Intent Switching

This experiment resolves the failure observed in v0.2.33.39: while a referential clarification was pending, the explicit request `AIを開発したい` was incorrectly treated as an answer to the question about which prior experiment to resume.

`InterruptibleDSSBridge` now checks `purpose_confidence_v02311.explicit_goal` on incoming turns while pending. A clearly detected new goal interrupts and clears the reference dialogue, rejects any unapproved candidate, then routes the utterance through the actual DSS purpose controller. A recognized topic switch also interrupts. Ambiguous replies stay on the clarification route. Approval still requires calling `confirm(True, context)` explicitly.

The reference ambiguity parser is still the narrow MockDSS; approved context memory is still an experimental shadow JSON store. Stable DSS/semantic files, model weights and /sleep are untouched.

## Run in Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.40
git pull origin v0.2.33.40
python -m py_compile clarification_interruption_v023340.py
python -m unittest -v test_clarification_interruption_v023340.py test_real_dss_reference_bridge_v023339.py
python clarification_interruption_v023340.py --demo
```

Results: `results/clarification_interruption_v023340.json` and `results/interrupt_shadow_v023340.json`. The experiment refuses to overwrite existing output.

## Known limitations

The goal-switch rule is a deterministic heuristic, not a calibrated intent classifier; indirect changes of topic may remain unresolved. Conversely, an explicit goal-like phrase given as a clarification answer may interrupt. Tests demonstrate policy handling, not general natural-language understanding. Cross-process writes to the shadow store have no transaction locking.
