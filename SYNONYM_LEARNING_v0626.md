# LLM_CHA v0.6.26 — Synonym Learning and Query Expansion

Synonym pairs are stored in `data/synonym_pairs_v0626.jsonl` as local,
user-approved lexical equivalence relations. The default seed is
`猫 = ネコ = ねこ`. No training of checkpoint weights is performed.

Runtime commands:

```text
/synonym-add 自動車 = クルマ
/synonym-list ネコ
```

When the user asks about a concept, retrieval tries:
1. Exact subject, then synonym subject candidates.
2. Exact raw-corpus phrase, then synonym phrases.
3. Existing Wikipedia/UNKNOWN paths when local evidence is absent.

Trust state restrictions on both the input and the synonym subject prevent
promotion of blocked records. Source passages are always marked unverified;
synonym pairs are never themselves facts about the world.

The number of expanded synonyms is capped at eight to prevent unbounded
search expansion. Learned pairs survive restarts in the local JSONL file.
There is no automatic synonym inference from arbitrary co-occurrence;
proposed ML-derived pairs should be reviewed before adding them.

```powershell
git pull --ff-only origin v0.6.26
python -m unittest -v test_synonym_lexicon_v0626.py test_raw_concept_evidence_v0615.py
python chat_window_v061.py --latest-experimental
```

Try `ネコ`, `猫`, and `/synonym-add 車 = 自動車` followed by
`/synonym-list 自動車`.

Note: literature/persona-specific routers may intercept cat-related prompts
before synonym-expanded subject search. This addition keeps those routes intact.
