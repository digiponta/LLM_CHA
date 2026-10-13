# LLM_CHA v0.4.24 — Opt-In Runtime Quality Capture

This adds the commands `/capture on`, `/capture off`, `/capture status` to `chat.py`.

- OFF by default and reset to OFF on next process start.
- Captures only the regular LLM generation branch after the model response is resolved, never commands, fixed identity/persona responses, Wikipedia lookup or canonical knowledge retrieval.
- Stores real original user questions, final displayed answers, observed agreement and semantic agreement, and original acceptance boolean; one UTF-8 no-BOM JSONL record per turn, in `results/persona_capture_new.jsonl`.
- Uses random unique capture IDs; appends instead of overwriting; 2MB size safety cap.
- Failures print capture ERROR and are not intended to affect the response.
- Does not touch weights, Semantic Memory, Truth Gate, `/train`, `/sleep` or existing learning settings.
- Contains potentially sensitive conversations: enable only for intentionally collected evaluation conversations, inspect and remove records you do not want retained or shared. Never auto-promote captures into training or independent holdout.

## Windows verification

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m unittest -v test_persona_quality_capture_v0424.py test_persona_quality_annotation_v0423.py test_persona_quality_benchmark_v0422.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
python chat.py
```

Inside chat:

```text
You> /capture status
You> /capture on
You> 読書は楽しいと思う？
You> /capture off
You> /exit
```

After the chat:

```powershell
Test-Path results/persona_capture_new.jsonl
Get-Content results/persona_capture_new.jsonl -Encoding UTF8
python persona_quality_annotation_v0423.py --captures results/persona_capture_new.jsonl --prepared results/persona_quality_pending_v0423.json
```

The file may contain earlier manually entered development examples. Segregate and deduplicate them before evaluation. Historical questions are excluded by the v0.4.23 default exclusions; newly captured questions are **not automatically independent**. Blind human labels and a sealed holdout remain necessary.

**Limitation:** running old integration suites cannot substitute for a live GPU chat/capture smoke test. This change has not been executed on the user's Windows GPU by the author.
