# LLM_CHA v0.9.7.25 — Context Robustness Diagnostics

This branch adds a six-way diagnostic using the currently loaded model.
The existing conversational and clipboard answer pathways remain unchanged.

A — ordinary canonical identity question.
B — unrelated weather sentence before the identity question.
C — related identity statement before the question.
D — preceding QA history using the current runtime's build_prompt.
E — inline semantic-style context before the question.
F — alternate identity question / paraphrase.

A-E contain the same final question. F differs in wording.
All use temperature 0, seed 42, top_k 3, repetition penalty 1.08 and
64 maximum output tokens. Report token counts, confidence, exact identity
string, and generated response. Exact identity mention is not equivalent
to grammatical fluency or ground truth.

**Important:** these are controlled probes, not independent holdouts,
and the model's historic SFT format has not yet been inspected. The
existing history selection routine may prune a prior exchange when it
judges it irrelevant; inspect the generated prompt if D behaves
unexpectedly. The diagnostic performs no training or auto-acceptance.

## Windows PowerShell

```powershell
git fetch origin
git switch --track origin/v0.9.7.25
python -m unittest -v test_context_robustness_diagnostics_v09725.py test_generation_capability_diagnostics_v09724.py
python chat.py
```

Then run:

```text
/context-robustness-audit
```

Interpretation: failures specifically in B/C/E implicate prefix/context
robustness, while D checks additional dialogue history. If even A/F fail,
return to checkpoint, tokenizer, and trained basic QA validation.
