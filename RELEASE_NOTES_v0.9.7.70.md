# v0.9.7.70 — Semantic Dialogue State (experimental)

Adds a nonpersistent structured representation of explicit positive preferences and sensory preference reasons:
- `semantic_dialogue_state_v09770.py`: `DialogueFrame` dataclass, `extract_preference`, `extract_reason`.
- `chat.py`: creates an ephemeral frame only when the existing PreferenceDialogue handler returns a response, then logs `[semantic_dialogue=...]` in CLI diagnostics.
- `test_semantic_dialogue_state_v09770.py`: 5 focused tests.

Example:
```text
You> 私は、スファレライトが好きです。
[semantic_dialogue={"topic":"スファレライト","intent":"express_preference", ...,"truth_state":"USER_REPORTED"}]
You> きらきらしてるところが心地よい
[semantic_dialogue={"topic":"スファレライト","intent":"explain_preference","attribute":"appearance","quality":"sparkling","emotion":"comfort",...}]
```

This is an experimental, rule-derived semantic frame, not an LLM semantic embedding or generic semantic inference. It is session-only and not used for training, external-evidence approval, or durable user-profile storage.

Windows verification:
```powershell
git fetch origin
git switch v0.9.7.70
git pull --ff-only
python -m unittest -v test_semantic_dialogue_state_v09770.py test_sensory_preference_v09769.py test_causal_question_normalization_v09765.py
python chat.py
```

Windows integration has not yet been tested.
