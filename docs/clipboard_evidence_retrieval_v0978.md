# LLM_CHA v0.9.7.8 — Clipboard Evidence Retrieval

A new **experimental diagnostic**, not automatic Semantic Memory ingestion or LLM
generation. It compares character bigram keyword overlap and TF-IDF cosine
rankings over distinct lines of manually copied Web text. Neither is a
Semantic Vector; the output labels that path `NOT_CONNECTED`.

Existing `フードには何がある？` and `フラペチーノの種類は？`
paths remain unchanged in this release.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.9.7.8
python -m unittest -v test_clipboard_evidence_retrieval_v0978.py test_clipboard_grounded_qa_v0977.py test_clipboard_context_v0976.py
python chat.py
```

After copying text from Chrome and entering `/read-clipboard`:

```text
You> /clipboard-retrieve フラペチーノの種類は？
You> /clipboard-compare フラペチーノの種類は？
```

Results include exact quotations from clipboard, retrieval score, original
line position and `EXTERNAL_UNVERIFIED` status. Scores are lexical relevance
only, not confidence of factual truth; do not promote retrieved data without
review. Follow-on work: independent relevance-labeled retrieval evaluation,
genuine LLM_SEM vector adapter, then grounded generation and answer audit.
