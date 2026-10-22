# LLM_CHA v0.6.37 — Synonym-Aware Approved QA Retrieval

When `--approved-qa-overlay` is supplied, the interactive `chat.py`
checks an exact approved question first. If no direct hit, it tries at most
32 distinct candidates formed by one substitution with pairs in the existing
`SynonymLexicon`. A lookup only succeeds when all matched approved records
agree on the same answer. A direct approved match takes precedence.

Unmatched or ambiguous queries **fall through** to the unchanged chat runtime,
including Truth Gate and Wikipedia fallback. No Wikipedia result is promoted
to approved knowledge. This does not update the model weights or synonym files.

## Execute

```powershell
git fetch origin
git switch --track origin/v0.6.37
python -m unittest -v test_approved_synonym_qa_v0637.py test_chat_approved_overlay_v0636.py test_memory_first_v0635.py
```

Example approved record in a **local test-only JSONL file**:

```json
{"question":"ネコとは","answer":"ネコは動物です。","source_id":"reviewed-example","status":"approved"}
```

```powershell
python chat.py --approved-qa-overlay data/my_approved_qa_test.jsonl
```

Ask `猫とは`: the router may find `ネコとは` through the known 猫/ネコ
lexical equivalence. Ask `猫` without a matching approved QA: it will
continue through the original Truth Gate and possibly Wikipedia path.
Do not confuse synonyms with merely related concepts.

This is bounded lexical substitution, not semantic inference, full QA
paraphrase matching or a replacement for existing Semantic Memory.
