# LLM_CHA v0.2.33.79 — Conversation Generalization Observations

v0.2.33.78 achieved **5/5 fixed acceptance patterns** on the user's GPU machine (the three exploratory cases were not scored). The new script `conversation_generalization_v023379.py` is intentionally **separate** from the passing baseline. It uses a copied checkout, Python UTF-8 pipes, and a real `chat.py` subprocess.

Eight exploratory turns probe greetings, repetition, the topic '宇宙', follow-up phrasing, GPU definition, a contrived unknown concept, acknowledgement, and ambiguous reference. The report stores per-turn answer text, route markers, rejection signals and a short raw excerpt.

**Important:** `observed` and `nonempty_answers` are logging coverage, not accuracy. The script does not yet measure false-rejection accuracy, topic persistence accuracy, persona consistency, or response semantic quality. Those require independent gold labels and human review. Runs may depend on local Truth State and model checkpoint.

## Windows verification

```powershell
git fetch origin
git switch v0.2.33.79
git pull origin v0.2.33.79
python -m py_compile conversation_generalization_v023379.py
python -m unittest -v test_conversation_generalization_v023379.py test_extended_chat_runtime_v023378.py
python extended_chat_runtime_v023378.py --run --timeout 240
python conversation_generalization_v023379.py --run --timeout 240
```

New report: `results/conversation_generalization_v023379.json`.

Show a quick per-case summary:

```powershell
$r = Get-Content results/conversation_generalization_v023379.json -Raw | ConvertFrom-Json
$r.probes | Format-Table id,category,observed,answer,rejected -AutoSize
```

No change to model weights or semantic truth records is intentionally made. GPU run results must be verified on the user's machine.
