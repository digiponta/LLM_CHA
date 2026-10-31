# v0.13.58.82.92 — RealPersonaChat Pair Audit

Observed local schema: 13,583 dialogue JSON files, eight sampled dialogues with 30 utterances each. Each utterance has utterance_id, interlocutor_id, text, timestamp; dialogues contain two interlocutor IDs and evaluation rows.

This version **does not export training samples** or start learning. It counts adjacent turns from *different speakers* as candidate user→assistant pairs and assigns a stable train/val/test partition by dialogue ID (80/10/10); the source text is not logged. Opposite-speaker pairs in both directions are **not automatically safe to mix as one persona**. Choosing a target speaker/persona and reviewing the source data's license, language, private information, and evaluation metadata must precede writing training data. A local conversation split prevents exact same-dialogue leakage but not semantic overlap across different dialogues.

Windows:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.92-real-persona-pairs
python -m unittest -v test_real_persona_pairs_v013588292.py
python audit_real_persona_pairs_v013588292.py --source data-src/real-persona-chat --max-dialogues 100
python audit_real_persona_pairs_v013588292.py --source data-src/real-persona-chat
```

Report: `results/real_persona_pair_audit_v013588292.json`. The first run is a smoke audit; the second scans all files and replaces the same report with full counts. Supply the summary (not raw conversation data) to determine speaker/target filtering. Production checkpoint is unchanged.
