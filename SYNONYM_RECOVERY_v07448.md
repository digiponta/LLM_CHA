# LLM_CHA v0.7.44.8 Synonym-Aware Recovery (CLI + GUI backend)

The single `chat.py` backend used by both CLI and `chat_gui_v07447.py`
now attempts a conservative bare-synonym Wikipedia recovery after a
LOW_SIGNAL_REJECT. Source and destination truth gates are checked. Any
retrieved text is labelled EXTERNAL_UNVERIFIED, is never automatically
promoted, and is not added to accepted history or learning.

## Windows PowerShell

```powershell
git pull
python -m unittest -v test_synonym_recovery_v07448.py test_synonym_runtime_wiring_v07448.py test_chat_gui_v07447.py test_persona_signal_wiring_v07446.py
$env:LLM_CHA_RESPONSE_GATE="1"
python chat_gui_v07447.py
```

Try `猫`, `ぬこ`, `ネコ`, `ぬことは`, `貴方の名前は`.
Expected for `ぬこ` when the learned synonym and Wikipedia lookup are
available: `synonym_recovery=FOUND` and
`response_quality_gate=SYNONYM_WIKIPEDIA_RECOVERY`.
If evidence cannot be retrieved, the nonfactual fallback remains.
This is only an opt-in recovery path; GPU acceptance/regression is pending.
