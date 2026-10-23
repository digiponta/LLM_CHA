# LLM_CHA v0.7.42 — Trusted Model-Only Generation Audit

The v0.7.41 teacher-forced NLL study found one Approved knowledge
fingerprint bound to the checkpoint, but did not test free generation.
The v0.7.42 script calls `LanguageModel.generate` directly, with
no `chat.py` routing, Wikipedia, Corpus Memory, or Experimental Adapter.
Decoding is greedy (temperature 0, repetition penalty 1) for repeatability.

Probes: one exact Approved question drawn from the synchronized Approved
Semantic ledger, two paraphrased vacuum tube questions, and five
existing-persona/AI/LLM/CUDA/quantum-mechanics questions.

Reports raw model output, exact-answer substring containment for the
Approved training prompt, and *keyword presence* for paraphrase/stability
probes. Keyword presence does not establish semantic accuracy.
No model weight or memory mutation occurs.

## PowerShell

```powershell
git fetch origin
git switch --track origin/v0.7.42
python -m unittest -v test_trusted_generation_v0742.py test_trusted_retention_v0741.py
python verify_trusted_generation_v0742.py
```

Report: `results/trusted_generation_v0742.json`

The current model is the post-sleep checkpoint. A before/after claim
requires an independently preserved pre-sleep checkpoint; v0.7.42
only measures the current checkpoint's free-generation capability.
