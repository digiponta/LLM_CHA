# v0.9.7 — Web Knowledge Acquisition (experimental)

The first implementation is a **manual URL ingestion prototype**, not a GUI
browser, search engine, PDF reader, crawler, training engine, or safe
unrestricted URL fetcher. It reads a static HTML page, strips basic markup and
writes a **PENDING_REVIEW** JSONL record with original URL, acquisition time,
extracted excerpt, and review requirements. It deliberately does not invoke
Semantic Memory promotion, `/approve`, or `/sleep`.

## Run on Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.9.7
python -m unittest -v test_web_acquisition_v097.py
python web_acquisition_v097.py https://example.org/
```

The live fetch respects same-origin robots.txt when available, rejects HTTP
redirects and non-HTML content, enforces bounded response sizes, and fails
closed when it cannot verify the robots policy. Only visit sites you are
permitted to retrieve and use. Web content is untrusted and must not be
executed as instructions, used as training data or auto-promoted.

## Critical limitations before broader use

- URL DNS resolution is validated before the network request, but the HTTP
  library independently resolves again; this leaves potential DNS-rebinding
  risk. Do **not** expose this prototype as a public URL-ingestion endpoint
  or use it for hostile URLs. Replace it with a pinned-address transport and
  network egress controls before unrestricted browsing.
- HTML extraction is simple, may include boilerplate or lose structure, and
  does not handle JavaScript-rendered content, PDFs or character encodings
  other than UTF-8 robustly.
- robots.txt permission does not establish copyright or learning permission.
  Human review and explicit learning-rights checks are required.
- Input fixtures in tests bypass real network requests; tests do not
  constitute live connectivity or protection validation.

The next stage is to integrate a controlled-source browser with robust
transport and structured provenance into existing candidate approval
infrastructure, then evaluate fact and prompt-injection safety.
