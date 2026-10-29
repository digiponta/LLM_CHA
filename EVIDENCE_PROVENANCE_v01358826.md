# LLM_CHA v0.13.58.82.6 — Evidence Provenance

## Changes
- TemporaryEvidence.add accepts source_title, source_url, and retrieved_at; stores UTC retrieval time by default.
- TemporaryEvidence.lookup returns topic, attribute, extracted value, exact matching quote, source fields and EXTERNAL_UNVERIFIED status.
- GUI shows an Evidence tab for the current in-memory records and appends the supporting quote under provenance-backed answers.
- Wikipedia records have a **search URL**, not a verified exact article URL; clipboard source URL is unknown. Do not misrepresent either as a verified primary source.
- Model inference, Semantic Memory, /sleep, and automatic knowledge promotion are unchanged.

## Run
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.6-evidence-provenance
python -m unittest -v test_evidence_provenance_v01358826.py test_evidence_attributes_v01358825.py test_temporary_evidence_v01358824.py
python chat_gui.py
```

## Limitations
This is still a label-matching prototype, not independent fact verification. User clipboard snippets remain unverified, and the GUI-only store does not sync to CLI chat.py. No automatic training or saving. Confirm Japanese text and answer quote rendering on Windows.
