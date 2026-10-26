# LLM_CHA v0.11.3 — standalone live-model Semantic Memory bridge

This is a **separate experimental CLI**, not a patch to Nagato's existing chat.py.
It loads the same frozen decoder factory from v0.10.1, uses Beam-3/48 and
retrieves corpus propositions via retrieval_first_runtime_v1012161.resolve_subject.

A corpus hit does **not** attest truth or approval. If generated and retrieved
text differ, it passes UNKNOWN to the v0.11.2 dialogue bridge, requesting a
user choice. A previous choice is only reused for an identical question and
candidate pair. No prompt reference text is used for reranking or approval.
The experimental tool does not write to Semantic Memory or alter model weights.

Run:
```powershell
git pull --ff-only
python -m unittest -v test_semantic_live_bridge_v0113.py
$env:LLM_CHA_DECODE_MODEL=(Resolve-Path ".\model\model-gpu-v1.6.2-online.pt").Path
python semantic_live_bridge_v0113.py
```

The command requires `data/subject_keyed_corpus_memory_v101216.jsonl`.
The CLI asks for an explicit subject if suffix heuristics are insufficient.
Use /exit to quit. The UI prints the stored choice for identical subsequent
question/candidates. For unknown facts, missing memory, or unrelated text,
manual input is not evidence of objective truth.

Next: inspect existing chat.py dispatch/Topic Context and truth-state layers
before embedding this functionality into production dialogue; implement a real
proposition-based equivalence checker and independent holdout.
