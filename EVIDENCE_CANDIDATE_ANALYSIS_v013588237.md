# v0.13.58.82.37 — Evidence Candidate Analysis

The dedicated evidence candidate route reached REJECT_NOT_ENTAILED with the original textual source shown as fallback. This release adds a diagnostic-only candidate-versus-source comparison: individual candidate sentences, substring-match flag, and highest SequenceMatcher ratio against source sentences. This is **not** semantic entailment or factual validation; no rejection rule is relaxed.

GUI `/gencandidates` prints up to three recent analyses (candidate text, source excerpt, source URL, Gate classification). Text is held only in the current process; no automatic persistence, promotion, or training. Because output includes raw excerpts and generated text, avoid sharing diagnostics containing sensitive material.

## Windows smoke test

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.37-candidate-analysis
python -m unittest -v test_evidence_candidate_analysis_v013588237.py test_evidence_aware_route_v013588236.py test_response_correlation_v013588235.py test_prompt_normalization_v013588234.py
python chat_gui.py
```

Conversation: `宇宙とは`, `CPU`, `宇宙の話に戻って`, `もう少し詳しく`, `/genstats`, `/gencandidates`. Compare candidate and source and classify the failure manually into genuinely unrelated, partial match, possible paraphrase, or contradiction. Do not infer verified entailment from lexical similarity.

Next: independent human-labeled benchmark and controlled baseline comparison rather than automatic adoption of high-similarity outputs.
