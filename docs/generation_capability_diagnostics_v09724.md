# LLM_CHA v0.9.7.24 — Generation Capability Diagnostics

A diagnostic-only audit of the already loaded language model, using its
existing `chat.build_prompt` function rather than guessed delimiters.

Three same-checkpoint generation cases:
- A_CANONICAL: known identity question without context
- B_SHORT_CONTEXT: same question preceded by a short statement
- C_LONG_CONTEXT: same question preceded by a longer repeated statement

The audit prints prompt token counts, generated text, confidence, and a
Tokenizer encode/decode roundtrip for Japanese inputs.

**Scope note:** This establishes compatibility with the *runtime's*
canonical prompt construction, not that the model's historical SFT
training format has been verified. Confirm the actual training
data/template separately before making such a claim. Known identity
prompts are probes and are not an independent held-out benchmark.

The diagnostic uses `temperature=0`, `seed=42`, and
`max_new_tokens=64`. It does not select generated answers, update the
chat's semantic state, promote facts, or train weights.

## Windows PowerShell
```powershell
git fetch origin
git switch --track origin/v0.9.7.24
python -m unittest -v test_generation_capability_diagnostics_v09724.py test_conversation_prompt_compatibility_v09723.py
python chat.py
```

Inside the CLI:
```text
/generation-capability-audit
```

Review A/B/C generation quality, confidence, prompt token lengths and
Japanese roundtrip integrity. If A already fails, investigate the model
checkpoint and SFT data before changing Semantic Context representation.
