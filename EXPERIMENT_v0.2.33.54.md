# LLM_CHA v0.2.33.54 — Session Reference ↔ Semantic Memory Safe Bridge

This branch adds an **opt-in, read-only** connection from a previously approved `SessionReferenceStore` record to the existing **atomic semantic proposition layer**, using the real `semantic_proposition_v1090.load_propositions` API. It does not append, promote, change truth states, train the LLM, or invoke `/sleep`.

## Boundary and provenance

The session reference (for example `cursor`) is a contextual pointer, **not** a verified scientific fact. Lookup requires both an approved, non-expired reference for the exact context and an existing atomic proposition with an **exact matching subject**. No arbitrary alias / subject mapping is inferred. Missing evidence produces an explicit no-evidence response; the system never invents a proposition to satisfy a reference.

Results are labeled as source `atomic_propositions_read_only`, with an **unverified truth/freshness warning**. A match in the atomic store is not an assurance of validity. This initial integration does not yet aggregate subject, typed, unified, internalized or truth overlays. It is a conservative first bridge.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.54
git pull origin v0.2.33.54
python -m py_compile chat.py safe_reference_semantic_bridge_v023354.py
python -m unittest -v test_safe_reference_semantic_bridge_v023354.py test_session_reference_stabilization_v023353.py
python chat.py --session-reference-memory
```

Interactive commands:

```text
You> 昨日の実験の続きをやって
You> カーソルでお願いします
You> はい
You> /refknowledge
You> /refstatus
```

`/refknowledge` reads the atomic proposition source from `--propositions` (the same path `chat.py` uses), but does not write it. If `cursor` is absent in that source, it displays a grounded no-evidence message.

## Caveats

This is **not merged into main** and is still behind `--session-reference-memory`. Real GPU `chat.py` end-to-end execution for this version has not been checked yet. Truth-aware policy and provenance aggregation via `SemanticKnowledgeArchitecture` are future extensions; no unreviewed reference is promoted into permanent knowledge.
