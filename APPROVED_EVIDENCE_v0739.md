# LLM_CHA v0.7.39 — Approved Evidence State in Runtime and GUI

v0.7.38 demonstrated that unchanged source knowledge is automatically
approved on the **11th** reference with a default threshold of 10.
v0.7.39 displays that operational approval in the source-evidence
answer path without treating it as externally verified scientific truth.

The dual-memory Approved JSONL store is the authoritative source of
operational approval status. On every CORPUS_MEMORY / RAW_CONCEPT_EVIDENCE
reference, the runtime resolves the exact source/answer identity against
the approved and candidate records and outputs:

```
[evidence_approval: state=APPROVED, count=-, factual_truth=UNVERIFIED]
```

The GUI shows `Source approval: APPROVED` separately from the answer route.
The original corpus response, Wikipedia citation, and independent Truth Gate
remain unchanged. The existing corpus and raw-evidence route is **not**
rewritten as a Trusted neural-model output.

## PowerShell

```powershell
git fetch origin
git switch --track origin/v0.7.39
python -m unittest -v test_approved_evidence_state_v0739.py test_evidence_reference_v0738.py test_reference_approval_v0737.py test_gui_status_v0733.py
$env:LLM_CHA_MEMORY_FIRST="1"
$env:LLM_CHA_MEMORY_FIRST_MODE="constrained"
$env:LLM_CHA_AUTO_APPROVE_REFERENCES="10"
python chat_window_v061.py
```

Expected 17 tests in total (2 + 5 + 5 + 5), pending local execution.

Approved source evidence is not yet trained into Trusted model weights. A
future integration would require an explicit policy for whether operational
approval is sufficient for inclusion in the Trusted Semantic Memory and
separate verification of factual truth. Source evidence approvals should not
be confused with the existing Truth Gate's independently managed truth state.
