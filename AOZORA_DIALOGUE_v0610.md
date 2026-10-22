# v0.6.10 — Stateful Literature Follow-up (opt-in)

Addresses observed dialogue:
- `吾輩` → identify *吾輩は猫である*
- `猫の名前は` → answer in the established literary context (unnamed cat)
- `猫` → ask which topic
- `一般的` → acknowledge animal/general topic, without unknown rejection
- `猫` → `作品` → resolve literary topic

Conservatively preserves chat.py other routes (長門, 宇宙, Wikipedia,
unknown teaching); slash commands are never intercepted. Context resides
only in current chat process. No modifications to Semantic Memory or weights.
The work lookup requires that the v0.6.4 corpus is present; absence disables
literature lookups. `猫の名前は` is a fixed verified-in-text literary
fact; evidence passage retrieval and multi-turn natural-language generation
are still future work.

```powershell
git fetch origin
git switch --track origin/v0.6.10
python -m unittest -v test_aozora_dialogue_v0610.py test_aozora_literature_router_v069.py test_chat_window_v061.py
$env:LLM_CHA_AOZORA_ROUTER="1"
python chat_window_v061.py --latest-experimental
```
