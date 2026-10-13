# LLM_CHA v0.3.7.3 — automatic Persona response

The `/persona CONCEPT` chat command has been removed. Persona evidence is now considered as part of **ordinary conversations**.

## Current response priority

1. Grounded follow-up and existing corpus-first retrieval stay intact.
2. Canonical and validated semantic retrieval remain on `AI>`.
3. If the dispatcher would `BLOCK` because `state=RAW_CORPUS_ONLY`, and there is actual raw-corpus evidence for its focus, return an attributed original excerpt with `persona>`.
4. Explicit truth-policy `BLOCK` still wins. If no persona evidence exists, preserve the existing fallback and teaching queue route.

Example:

```text
You> 量子力学とは
persona> この人格の原文には、次のような考えが記されています。...
[persona-evidence id=..., line=..., state=PERSONA_STATEMENT, factual_truth=NOT_ASSESSED]
[persona-route=RAW_CORPUS_ONLY, source-grounded, factual-truth-unchanged]
```

A line starting `persona>` identifies an attributed persona-source response; it is not automatically a factual truth. Existing `AI>` routes retain their current prompts. This stage is **not** a generative persona model and does not automatically classify every question as a persona question. Corpus Memory results sourced from `data-nagato.txt` continue to use existing `AI>` until a separate compatibility-tested labeling change. Slash `/means` remains available.

## Run

```powershell
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m unittest -v test_persona_semantic_memory_v0371.py test_auto_persona_route_v0373.py test_means_centric_semantics_v0372.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
python chat.py
```

Try `量子力学とは`, `数学とは`, `CPUとは`, `宇宙とは`, `宇宙の話に戻って`, `もう少し詳しく` and `文学とは`.

**Scope:** Rule-based raw-corpus fallback, source quoting, opt-in experimental branch only. No changes to checkpoint, factual Truth Gate, source files, or truth states.
