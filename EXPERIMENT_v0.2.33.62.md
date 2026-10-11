# LLM_CHA v0.2.33.62 — Session Reference ↔ Multi-Proposition Evidence Bridge

## Purpose

This opt-in branch connects the **real SQLite Session Reference Store**, explicitly approved **Reference-to-Concept Mapping**, and **existing atomic proposition JSONL file** to the multi-proposition proof-chain validator from v0.2.33.61.

It **does not** infer `TRUE` from the mere existence of a proposition. Every proof premise must appear both in the atomic proposition store (exact `subject + は + value` match) and in an **explicit, version-1 evidence manifest** with `truth: "TRUE"`, a nonempty `source`, and an evidence ID. The manifest must explicitly authorize `["includes"]` transitivity. This is a review claim, not independent proof of factual correctness.

The `/refchain` command requires an approved current session reference, approved and unexpired mapping, and an inference candidate whose subject is precisely the mapped concept. It shows the ordered supporting evidence IDs or a blocking reason, never writes to Semantic Memory and never invokes `/sleep`.

## PowerShell

```powershell
git fetch origin
git switch v0.2.33.62
git pull origin v0.2.33.62
python -m py_compile chat.py session_multi_evidence_bridge_v023362.py
python -m unittest -v test_session_multi_evidence_bridge_v023362.py test_multi_proposition_evidence_v023361.py
python chat.py --session-reference-memory
```

If the user has not created a reviewed evidence manifest, `/refchain AはCを含む` responds `no_evidence_manifest`. **Do not alter the production proposition store merely to make this test pass.** All positive-path test records are created in a `TemporaryDirectory`, isolated from the live repository's `data` directory.

Example *isolated* atomic propositions:

```jsonl
{"subject":"A","value":"Bを含む"}
{"subject":"B","value":"Cを含む"}
```

Example reviewed fixture manifest (schema v1, explicit transitivity authorization):

```json
{
  "schema": 1,
  "transitive_relations": ["includes"],
  "evidence": [
    {"statement": "AはBを含む", "truth": "TRUE", "source": "local reviewed test", "evidence_id": "e1"},
    {"statement": "BはCを含む", "truth": "TRUE", "source": "local reviewed test", "evidence_id": "e2"}
  ]
}
```

Configure an isolated file through `--multi-evidence-manifest` and atomic records through `--propositions`. Once `cursor` is approved and mapped explicitly to the concept `A`, `/refchain AはCを含む` should return evidence IDs `e1 → e2`. These examples are artificial formal relations, **not independent factual knowledge**.

## Limits / next investigation

- The source inventory is the atomic proposition JSONL; subject/typed/unified/provenance Truth State layers are not automatically imported.
- The manifest is an explicitly curated local assertion; there is no cryptographic binding, reviewer signature, document retrieval, or independent truth adjudication. Not appropriate for high-trust knowledge claims.
- The existing proof-chain validator checks direct negative counterevidence for the requested pair and identical conditions; it does not detect all contradictions or logical entailment errors.
- Successful artificial fixtures do not establish a production GPU-generated answer.
- Not merged into main. No semantic-memory writes, training or changes to `/sleep`.
