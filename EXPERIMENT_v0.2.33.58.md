# LLM_CHA v0.2.33.58 — Evidence-to-Answer Consistency Validation

## Scope

Adds the opt-in `/refconsistent` command to the actual `chat.py`. It validates all earlier approvals, Truth State, dispatcher action and provenance gate **before** assessing whether the candidate answer is an exact normalized match to the source provenance's `evidence` text.

This is intentionally conservative: a subset, paraphrase, extra sentence, an empty evidence field, or a contradictory statement must not be silently called supported. The only normalization currently permitted is Unicode NFKC, whitespace at the edges and trailing punctuation. This is **not** natural language entailment or independent fact checking.

## PowerShell

```powershell
git fetch origin
git switch v0.2.33.58
git pull origin v0.2.33.58
python -m py_compile chat.py evidence_answer_consistency_v023358.py
python -m unittest -v test_evidence_answer_consistency_v023358.py test_evidence_grounded_reference_v023357.py
python chat.py --session-reference-memory
```

After explicitly approving an experiment reference and its mapped concept:
```text
You> /refmapped
You> /refevidence
You> /refconsistent
```

The current `RAW_CORPUS_ONLY / UNVERIFIED` case should be blocked with `truth_not_true`. Full positive-path coverage is provided through isolated semantic-result fixtures in the unittest module. Real-world validation requires reviewed source documents; a manually entered TRUE flag and evidence string do not establish factual correctness.

No writes to the proposition store, no LLM training or `/sleep`; this is not merged into main.
