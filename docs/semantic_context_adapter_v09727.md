# LLM_CHA v0.9.7.27 — Semantic Context Adapter Ablation

The semantic memory state remains ephemeral and source-attributed.
This diagnostic compares five approaches to inject short information
into the existing model without teaching the model new facts.

A_INLINE: compact typed data inside a single utterance.
B_DIALOGUE: short alias plus synthetic two-turn conversation.
C_SHORT_ALIAS: short natural-language alias context.
D_RETRIEVED: only up to two user-reported taste categories.
E_HYBRID: dialogue about alias and up to two taste categories.

Because previous tests showed the full product name and typed prefixes
could derail generation, only a brief alias is provided to the model.
The full entity remains available in the separate semantic state.

**Limitations:** B/E dialogue is *synthetic*, not a historical transcript.
"D_RETRIEVED" is heuristic extraction of reported attribute labels, not
semantic retrieval or verified factual evidence. E has no runtime gate
yet; every output is experimental and must not auto-replace the
existing ClipboardDialogue answer. Variant results may not be directly
comparable to the earlier canonical identity question tests because
this version asks an open-ended experience question.

## Windows PowerShell
```powershell
git fetch origin
git switch --track origin/v0.9.7.27
python -m unittest -v test_semantic_context_adapter_v09727.py test_semantic_context_isolation_v09726.py
python chat.py
```

Read the same clipboard menu, report the experience and taste details,
then:
```text
/semantic-adapter-audit その体験についてどう思う？
```

The command prints all prompts and outputs for A-E with confidence,
token counts, and diagnostic-only flags. No training or persistence.
