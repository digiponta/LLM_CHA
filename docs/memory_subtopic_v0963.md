# v0.9.6.3 — Memory subtopic evidence experiment

This incremental branch adds a **lexical** subtopic classifier for statements in
`data/data-nagato.txt`, a deterministic evidence-anchored candidate
construction and the v0.9.6 quality-gate comparison. It does **not** yet
connect a new LLM decoding adapter, produce an LLM opinion, or alter normal
responses. Evidence is unverified. The sample answer is labelled
`DETERMINISTIC_TEMPLATE_NOT_LLM`.

Windows PowerShell:
```powershell
git fetch origin
git switch --track origin/v0.9.6.3
python -m unittest -v test_memory_subtopic_v0963.py test_wiki_selection_corpus_v0962.py test_context_routing_fix_v0961.py test_context_aware_response_v095.py test_grounded_generation_gate_v096.py
python chat.py
```

Within chat, run `/cha-memory-subtopics` to inspect provenance-preserving
corpus matches, and `/cha-memory-eval` to compare a deterministic candidate
with the existing safe baseline. These diagnostic commands do not train or
promote knowledge.

Next stage: produce *real* candidate text via a checkpointed model,
record tokenizer/checkpoint/generation settings, and run independent
held-out comparison. Quality-gate acceptance does not imply factual
verification.
