# LLM_CHA v0.13.58.83.08 — RSE independent-dialogue review queue

This branch samples source **test-split** dialogues using the same deterministic dialogue-level split as the v0.92 audit. It produces a metadata-only queue for human labeling; no plaintext is saved to the report. Sampling from the source corpus is NOT an independently sourced holdout, because all cases originate from RealPersonaChat and the same subject CP. It is independent at the split-dialogue level from the v0.93 train-only CP pilot.

Windows:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.08-rse-independent-holdout
python -m unittest -v test_rse_holdout_v013588308.py test_rse_accept_candidate_v013588307.py
python prepare_rse_holdout_v013588308.py --source data-src/real-persona-chat --speaker CP --split test --limit 30
```

Optional local inspection (do not upload raw conversation output):
```powershell
python prepare_rse_holdout_v013588308.py --source data-src/real-persona-chat --speaker CP --split test --limit 30 --show-text
```

Output: results/rse_independent_holdout_v013588308.json. It contains IDs, dialogue IDs and lengths, not sensitive text. All labels are null: they are **not** independently assessed by the script.

NEXT: create independently authored user questions for those source pairs; label answer suitability and speaker-experience risk locally; assess the Selection Gate on **both positive and negative** cases without using labels to tune the evaluation set. Note that simply labeling a RealPersonaChat source question-answer pair as suitable may overestimate question-answer matching performance: independently phrased test queries are essential.

This version does not modify chat.py, model checkpoints, or acceptance behavior.
