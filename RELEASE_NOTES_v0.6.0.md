# LLM_CHA v0.6.0 — Wikipedia Grounded Dialogue Stable Baseline

Release date: 2026-10-15

## Summary

v0.6.0 establishes a reproducible baseline for evidence-grounded, persona-aware Wikipedia conversations on top of the LLM_TRY v10.16.5 conditional semantic runtime. The v0.5.0 development branch remains the comparison baseline; v0.6.0 is a branch snapshot of that work.

## Features

- Wikipedia fallback for unknown concepts (`UNKNOWN_WIKIPEDIA_FALLBACK`).
- Topic-aware Wikipedia follow-ups (`PERSONA_WIKIPEDIA_TOPIC_FOLLOWUP`).
- Sequential, non-repeating evidence from the same article (`PERSONA_WIKIPEDIA_EVIDENCE_SESSION`).
- Bounded continuation to linked articles that explicitly mention the original topic (`PERSONA_WIKIPEDIA_EVIDENCE_CONTINUATION`).
- Mathematical expressions displayed as `LATEX( raw formula )`, without TeX rendering or mathematical interpretation.
- Provenance for Wikipedia answers, and safeguards preserving `EXTERNAL_UNVERIFIED`, `verified=False`, `train_ready=False`, and `auto_promote=False`.

## Verification

The user-reported Windows / Python 3.13 / NVIDIA GeForce RTX 3070 Ti run passed **60/60 targeted unit tests** on 2026-10-15:

```powershell
python -m unittest -v `
  test_wiki_evidence_continuation_v0564.py `
  test_wiki_evidence_session_v0562.py `
  test_wiki_more_details_v0560.py `
  test_persona_wiki_topic_followup_v0558.py `
  test_unknown_wiki_fallback_v0557.py `
  test_persona_auto_wiki_v0556.py
```

Manual runtime conversation: “量子ビットとは？” → “量子重ね合わせについて教えて” → “もっと詳しく” three times. The first two detailed follow-ups retrieved different evidence spans from the original article; the third retrieved additional evidence from the linked Wikipedia article 「アンサンブル解釈」. This is a *scoped* verification, not exhaustive performance, quality, security, or scientific-truth validation.

## Architecture

User input → normalization / intent routing / Known–Unknown gate → core semantic and conversation runtime → Wikipedia lookup / topic follow-up / same-article evidence session → linked-article evidence continuation → provenance and truth-state guard → user-visible answer.

Internal stores include the semantic proposition DB, subject and typed-subject indexes, conditional propositions, corpus memory, and truth-state / provenance metadata. Explicit learning and sleep workflows remain separate from automatic external Wikipedia retrieval.

## Limitations

- Word overlap with the original title is a conservative but incomplete relevance check for linked-article evidence.
- Related articles may describe alternative interpretations, not universally accepted scientific facts.
- Repetition detection is exact-span / source based, not a semantic paraphrase detector.
- Evidence ranking, multi-article context management, and heading/whitespace polishing are future work.
- Wikipedia answers are unverified external evidence and must not automatically train or promote model knowledge.
- This release does not assert end-to-end correctness for all question types or comprehensive model training validation.
