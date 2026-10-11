# LLM_CHA v0.2.33.60 — Semantic Memory Structural Evidence Integration

This experimental branch adds an **isolated positive/negative diagnostic suite** for the approved session-reference → verified concept mapping → Evidence Gate → Structural Consistency Gate pipeline.

The actual SQLite SessionReferenceStore and VerifiedConceptMapping implementations and real StructuralReferenceBridge logic are exercised. The semantic resolver is a deterministic **fixture facade** returning SemanticKnowledgeResult-shaped values with structured provenance; this is **not evidence that live SemanticKnowledgeArchitecture has a validated TRUE answer**, and not a GPU generation benchmark.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.33.60
git pull origin v0.2.33.60
python -m py_compile structural_evidence_integration_v023360.py
python -m unittest -v test_structural_evidence_integration_v023360.py test_structural_semantic_consistency_v023359.py test_evidence_answer_consistency_v023358.py
python structural_evidence_integration_v023360.py
```

The report defaults to `results/structural_evidence_integration_v023360.json`, refusing to overwrite an existing report. Expected result: **11/11 PASS** across three structural matches, relation reversal, polarity mismatch, dropped condition, UNVERIFIED truth, RAW_CORPUS_ONLY, unsupported grammar, context isolation, and mapping invalidation.

To additionally verify that the GPU chat runtime still works, run `python chat.py --session-reference-memory` and test `/refstatus`, `/refmapped`, `/refevidence`, `/refstructural`. The current live quantum-mechanics example is still expected to stop at `truth_not_true`.

**Limitations:** Does not create verified factual knowledge in production Semantic Memory. Does not perform document-based truth adjudication, multi-proposition composition, model-internal learning, or invoke `/sleep`. A positive fixture demonstrates that the gated code path is reachable with supplied evidence metadata, not that the supplied proposition is objectively true.
