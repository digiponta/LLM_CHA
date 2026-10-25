# LLM_CHA v0.9.7.23 — Prompt Compatibility Ablation

Five diagnostic-only prompt shapes compare the actual loaded checkpoint
under the same greedy sampling settings. Ordinary chat remains unchanged.

- **A_BASELINE**: question alone
- **B_STRUCTURED**: typed semantic state rendered as tagged context
- **C_NATURAL**: user-attributed semantic state in concise natural Japanese
- **D_DIALOGUE_RECONSTRUCTION**: schematic dialogue *derived* from semantic
  fields; it is NOT a verbatim conversation transcript
- **E_NAGATO_CHAT_STYLE**: a hypothesis for conversational prompt formatting,
  NOT verified against the model's exact SFT training template

All replies are diagnostic and rejected for automatic selection.
The report includes exact entity string presence and token/character counts,
which are *not* reliable proxies for semantic fidelity or fluency.
The current natural language rendering records that acidity, sweetness,
and chocolate were mentioned; it does not invent polarity or intensity.
Never treat a synthetic dialogue prompt as evidence of what was literally said.

## Windows PowerShell
```powershell
git fetch origin
git switch --track origin/v0.9.7.23
python -m unittest -v test_conversation_prompt_compatibility_v09723.py test_conversation_semantic_generation_v09722.py test_conversation_semantic_state_v09721.py
python chat.py
```

After `/read-clipboard` and the established experience/taste/conclusion
sequence, run:

```text
/conversation-prompt-compare その体験についてどう思う？
```

Compare five outputs for fluent Japanese, relevant response, preservation
of user-report provenance, unsupported claims, and output stability. A later
revision should compare against the **actual** learned prompt format by
inspecting training data and add held-out repeats.
