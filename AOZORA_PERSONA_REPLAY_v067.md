# LLM_CHA v0.6.7 — Aozora + persona replay experiment

This experiment starts **again from the v94 baseline**, not the persona-degraded
v0.6.5 Aozora checkpoint. It alternates updates from Aozora literature (next
token LM loss) and replay dialogue (assistant-response masked loss). Default
sampling probability is 50% replay / 50% literature, *per optimizer step*.

The two works are held apart: 789 (吾輩は猫である) is literature training,
1567 (走れメロス) is independent literature validation. A separate 15% of
deduplicated persona pairs are held out from replay training. This limited
experiment does not verify all Persona/Truth Gate/chat runtime behavior.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.6.7
# If the branch is already present locally: git switch v0.6.7
python -m unittest -v test_aozora_persona_replay_v067.py
python train_aozora_persona_replay_v067.py --dry-run
python train_aozora_persona_replay_v067.py --epochs 2 --max-steps 160 --persona-ratio 0.5
Get-Content results/aozora_replay_v067.json -Encoding utf8
```

Required input:
- `model/model-llm-try-nagato-chat-v94.pt`
- `model/tokenizer-v0.7-bpe.json`
- `data/aozora_v064/aozora_semantic_corpus.jsonl`
- `data/conversation-ja.txt` (default replay source: consecutive `人:` and
  `AI:` lines). Alternatively specify `--persona-data some_pairs.jsonl`
  with `{"user":"...","assistant":"..."}` records.

Outputs (never silently overwrite):
- `model/model-llm-cha-aozora-replay-v067.pt`
- `results/aozora_replay_v067.json`

Review `identity_answer`, `persona_holdout_nll` and `heldout_nll` before
using the experimental checkpoint. Identity alone does not validate the whole
persona. Next run `chat.py` with the resulting model and your existing
Truth Gate regression suite. Existing model files and Semantic Memory remain
unmodified. Replay data quality and representation are important; check the
input pair counts from the dry run. Use distinct output/report names for
further sampling-ratio experiments.
