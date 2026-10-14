# LLM_CHA v0.4.28.39 — Japanese QA Candidate Quality Gate

This standalone tool audits the previously generated v0.4.28.38 JSON without rewriting source text. All 26 candidates are unverified and must remain outside the training and evaluation pipelines.

### Policies
- `REJECT`: prior `identity` rule (erroneously infers identity from ordinary self-references), unsupported generation rules, missing explicit single-clause preference, ambiguity or compounded/conjoined topics.
- `HOLD`: a simple explicit preference clause with a conservative proposed question. `HOLD` means *requires human review*, never training-ready.
- `ACCEPT`: defined as a potential subsequent human-review outcome, never automatically issued.
- Original question, answer, candidate ID, source file/line and old rule remain in the output. Normalized `suggested_question` is an additional suggestion, not a verified ground truth claim.

### Commands (Windows PowerShell)
```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile gate_japanese_foundation_qa_v042839.py
python -m unittest -v test_gate_japanese_foundation_qa_v042839.py test_build_japanese_foundation_qa_v042838.py
python gate_japanese_foundation_qa_v042839.py `
  --input results/japanese_foundation_qa_candidates_v042838.json `
  --output results/japanese_foundation_qa_quality_v042839.json
```

Expected 15 tests: 8 new plus 7 previous. Actual local execution has not yet been performed by the user. The output reports `total`, `accepted`, `held`, `rejected` and detailed candidate reasons. Under current rules `accepted=0` by design.

### Limits and next stage
The initial 26 candidates do not reliably represent independent well-formed QA ground truth. The rule-driven status is a provisional structural check, not adjudication of semantics, factuality, safety, privacy or licensing. Next: human review of HOLD, intentional sampling for variety, independently constructed Negative/Hard Negative pairs with explicit reference annotations, and independent held-out evaluation. **Never train from HOLD/REJECT or use as Gold labels.** This release does not alter source corpus, active Truth Gate, LLM weights, Semantic Memory, /sleep, /train, or chat.py.
