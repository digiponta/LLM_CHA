# LLM_CHA v0.9.7.22 — Semantic Context Generation Ablation

A diagnostic-only comparison of three prompt variants using the **same
already-loaded model** and fixed deterministic sampling configuration:

- A_BASELINE: ordinary question only
- B_SEMANTIC: question + ephemeral, provenance-aware conversational summary
- C_EVIDENCE_SEMANTIC: question + source-listed entity + conversational summary

Generated replies are **not adopted as chat answers**, trained, approved,
or written to Semantic Memory. The experiment returns token counts, topic
string presence, prompt sizes, and generated text for manual inspection.
These metrics do NOT measure grounding, correctness, or language fluency.

The currently formatted semantic context preserves the user's subjective
report with source attribution; it never transforms clipboard content into
verified truth. This is a baseline integration experiment, not an LLM
accuracy claim.

## Windows
```powershell
git fetch origin
git switch --track origin/v0.9.7.22
python -m unittest -v test_conversation_semantic_generation_v09722.py test_conversation_semantic_state_v09721.py
python chat.py
```
Copy the menu and issue `/read-clipboard`, then:
```text
黒耳を飲んだ
酸味と甘さのバランスが良かった
黒耳は、ブラックチョコレートで甘かった
満足した
/conversation-semantic-status
/conversation-semantic-compare その体験についてどう思う？
```
Compare the three `trials` and note whether the LLM generates
plausible Japanese, topic-relevant content, or unrelated fragments.
