# LLM_CHA v0.3.7.1 — Persona Semantic Memory (first experimental slice)

The character's beliefs and hypotheses in `data/data-nagato.txt` are primary persona evidence, *not* automatically verified scientific facts. This version adds an explicit `/persona CONCEPT` interaction. It extracts sentence fragments containing the concept and replies as an **attributed quotation from the persona's source**, including stable excerpt IDs and source line numbers.

New files: `persona_semantic_memory_v0371.py`, `test_persona_semantic_memory_v0371.py`. `chat.py` now routes only the explicit `/persona ` command to this read-only evidence path. It **does not** train the checkpoint, promote semantic truth records, alter Truth Gate, or modify the default non-command question route. The response is an attributed excerpt, not a reliable synthesis of a complex worldview. Future improvements must provide context-aware, non-extractive, persona-consistent dialogue and evaluate faithfulness.

## Run on Windows PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m unittest -v test_persona_semantic_memory_v0371.py
python verify_integration_v0366.py --gpu --legacy --timeout 240
python chat.py
```

In chat:

```text
/persona 量子力学
/persona 数学
/persona 宇宙
/semantic 量子力学
```

The first three answer from persona source with `PERSONA_STATEMENT` / `NOT_ASSESSED` annotations. The last shows the existing factual knowledge route separately, expected to remain `RAW_CORPUS_ONLY` if no factual proposition was registered.

**Stage limitations:** This is a safe first step toward Persona Semantic Memory, not yet a persistent semantic vector store or an inference-time persona priority router. The evidence is literal substring search, so a term can occur in a negative context or in a thought experiment, and fragments should not be interpreted as independently verified assertions. Next: separate persona knowledge state `PERSONA_KNOWN` from `FACT_VERIFIED`, assess topical retrieval quality, and add opt-in persona-aware non-command routing with regression and GPU checks.
