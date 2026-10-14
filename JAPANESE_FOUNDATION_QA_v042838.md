# LLM_CHA v0.4.28.38 — Japanese Foundation Semantic QA Candidate Expansion

Previously, v0.4.28.37 produced only one rule-based positive candidate from 4,600 isolated utterances. This release adds an **auditable review-only pool** with wider explicit Japanese self-preference constructions, dislike statements, a conservative self-description rule, and role counts (QUESTION, GREETING, PREFERENCE, STATEMENT, OTHER). Every generated question cites its source line and rule.

**Not a conversational corpus:** each line is a standalone utterance. Adjacent lines must never be treated as paired turns. **Not gold QA:** candidates are marked RULE_PROPOSAL, `human_verified=false`, `review_required=true`, `usage=REVIEW_ONLY`. No automatic negatives, hard negatives, training or test splits are created. The self-description rule is intentionally provisional and particularly needs human review. The PII pattern is a minimal heuristic, **not** an assurance of anonymization; review sensitive biographical statements and verify dataset license before use.

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0

python -m py_compile build_japanese_foundation_qa_v042838.py
python -m unittest -v test_build_japanese_foundation_qa_v042838.py test_build_japanese_foundation_qa_v042837.py

python build_japanese_foundation_qa_v042838.py `
  --input data/japanese_foundation_v0218.txt `
  --output results/japanese_foundation_qa_candidates_v042838.json
```

Expected focused tests: 13 (7 new + 6 previous), Windows execution pending. Review total candidate counts, class mix, quality and ambiguous pronouns before any learning. Next experiment: manually adjudicate stratified positive proposals, construct counterfactual negatives with source-supported incompatibility, audit leakage across splits, and retain an independent human-reviewed QA test set.

No changes to `data/japanese_foundation_v0218.txt`, production Truth Gate, model weights, Semantic Memory, /sleep, /train, or chat.py.
