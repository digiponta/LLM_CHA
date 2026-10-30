# LLM_CHA v0.13.58.82.56 — Question–Evidence Relation Binding

This branch adds conservative, **offline-only** subject/relation/value binding on top of the v0.13.58.82.55 question-aware extraction. It addresses three false positives observed in the user's evaluation: (1) answering "宇宙とは" with the definition of *ビッグバン*, (2) answering the time of the Big Bang with a 20th-century history sentence, and (3) treating a description of expansion as an explanation of its cause.

The new `evidence_relation_binding_v013588256.py` supports a narrow set of subjects and relation cues. Time binding for the Big Bang requires a '億年前' age phrase in the context of the event (including immediately local anaphoric wording 'その時刻'). The cause/mechanism relations deliberately abstain until reliable event/causal role binding is implemented. The selected sentence must still pass the existing strict source-substring Evidence Gate. Unknown subjects, unsupported relations and absent values all abstain.

**Limitations:** This is heuristic relation binding, not semantic entailment. Anaphora is not fully resolved and event occurrence dates are not independently verified. Source text remains EXTERNAL_UNVERIFIED. A copied statement's matching words do not establish that it is scientifically correct. The checkpoint, runtime GUI, positive-teacher policy, and production decoding path are all unchanged.

## Windows PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.56-relation-binding
python -m unittest -v test_evidence_relation_binding_v013588256.py test_question_aware_evidence_v013588255.py
python evaluate_relation_binding_v013588256.py `
  --evidence-json results/evidence_snapshot_v013588249.json `
  --output results/evidence_relation_binding_v013588256.json
Get-Content results/evidence_relation_binding_v013588256.json -Encoding UTF8
```

Inspect `previous_sentence` vs `selected_sentence` for all four default questions. Expected target on this evidence snapshot: abstain for '宇宙とは', accept a Big Bang age passage containing '138.2億年前' for 'ビッグバンはいつ', abstain for '宇宙はなぜ', abstain for '宇宙の化学組成'. Evaluate with separate held-out sources before integrating into GUI.
