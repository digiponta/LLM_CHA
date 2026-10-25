# v0.9.4.3 — Question-Aware Evidence Selection

Role labels are textual relevance assessments only, not assertions of truth.
For explicit definition questions, direct definitions are preferred, followed
by subject relations and topical discussion. Incidental mentions are not
rendered as definitions. Subject relations in the Nagato corpus remain
preserved verbatim and unverified; Wikipedia remains independently sourced.

Windows PowerShell:
```powershell
git fetch origin
git switch --track origin/v0.9.4.3
python -m unittest -v test_question_aware_evidence_v0943.py test_corpus_role_classifier_v0942.py test_explicit_topic_corpus_v0941.py test_response_quality_v094.py test_topic_suggestion_followup_v093.py test_topic_suggestion_v092.py test_corpus_answer_plan_v091.py
python chat.py
```
Then ask `数学とは`, `文学とは`, and `量子力学とは`.
No model weights, Semantic Memory approvals, or raw corpus files change.
