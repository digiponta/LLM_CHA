# v0.7.44.18 Stable Proposition ID Migration

The `CorpusMemoryRecord` schema has an optional trailing `proposition_id`
field, so existing six-positional-argument constructors remain valid.
`normalize_record` loads an explicit ID when provided, otherwise derives
a deterministic SHA-256-based ID from normalized subject, statement,
and source. The ID is content-derived and changes when those fields change;
it is *stable across save/load and rebuilds of unchanged data*, not a
semantic-identity guarantee across edits.

The JSONL writer now includes `proposition_id`; historical rows can still
be loaded without editing them. Conflicting ID reuse is rejected.
No checkpoint, weights, approval state or trusted truth are modified.

```powershell
git pull
python -m unittest -v test_stable_proposition_id_v074418.py test_corpus_cursor_bridge_v074417.py test_evidence_cursor_v074416.py
```

The existing bridge's legacy-instance test remains valid (a manually
constructed six-field record lacks an ID); rows decoded by `load_memory`
now have stable IDs and can pass its READY preflight if source is present.

The runtime cursor remains unconnected until an integration test verifies
all initial-response statements were marked already presented. Do not
infer unseen evidence from text splitting.
