# v0.13.58.82.39 — Rejected Answer Repair and Verified Learning Preparation

An Evidence-Gate rejection now creates a local, unapproved repair record. It includes question topic, rejected candidate, rejection reason, retrieved external excerpt and URL, a proposed answer slot, and a state machine. Current external material is labeled EVIDENCE but remains EXTERNAL_UNVERIFIED; the system does not certify it as a correct reference.

States: PENDING_REPAIR -> PENDING_REVIEW -> APPROVED, or PENDING_REPAIR/PENDING_REVIEW -> REJECTED. The only way to mark APPROVED is explicit GUI `/repair approve ID`; no automatic learning or /sleep occurs. Approval means the user explicitly authorized the proposed answer for **experimental training candidate export**, not independently validated truth.

GUI commands:
- `/repair list`
- `/repair propose UUID 回答文`
- `/repair approve UUID`
- `/repair reject UUID`
- `/repair export` writes only approved candidate pairs to `results/repair_training_candidates_v013588239.json`.

Data is recorded to `data/rejected_answer_repairs.jsonl`. This can include locally sensitive queries and generated answers, so keep the file local and out of public Git history. This version intentionally does not integrate approved repair candidates into Semantic Memory, incremental learning, /sleep, or checkpoints: separate controlled evaluation must precede that. The original Evidence Gate remains unchanged.

## Windows verification

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.39-rejected-answer-repair
python -m unittest -v test_rejected_answer_repair_v013588239.py test_evidence_candidate_analysis_v013588237.py test_evidence_aware_route_v013588236.py
python chat_gui.py
```

Test: `宇宙とは`, `CPU`, `宇宙の話に戻って`, `もう少し詳しく`, then `/repair list`. Only after checking the source and correcting the proposed answer should you use `/repair propose ID ...` and `/repair approve ID`. `/repair export` creates a **candidate** dataset; it is not loaded automatically. Check heldout independence before experimental fine-tuning.

Known limitations: question captured from the Topic Context is currently the topic key rather than a complete original user utterance; the repair queue should eventually preserve explicit user question and context snapshot. Approval cannot substitute for an independent factual audit. No forgetting or persona regression comparison is implemented in this release.
