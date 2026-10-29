# v0.13.58.82.9 — Causal Evidence Retrieval

Adds a **conservative, quote-only** causal retrieval path in the GUI. It recognizes reason questions such as 「なぜカットが難しい？」, restores the currently active topic, and searches session-only clipboard/Wikipedia evidence for a **single explicit line** that contains the target, a stated material cause (hardness/cleavage/brittleness), and a causal connective such as 「ため」「ので」.

An accepted quote is displayed verbatim with the source marked EXTERNAL_UNVERIFIED. If an explicit causal statement is absent, the GUI says evidence is insufficient rather than guessing. The original LLM handles unrelated non-causal questions; existing social replies, general retrieval, and property answers remain available. No external snippets are promoted to Semantic Memory or trained.

Limitations: This initial experiment is narrowly tuned to *cutting difficulty* and Japanese connective markers; it does not synthesize a causal conclusion from scattered facts, handle general causal questions, cross-document contradictions, or judge the truth of an unverified source.

## Windows regression
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.9-causal-evidence-retrieval
python -m unittest -v test_causal_evidence_retrieval_v01358829.py test_social_dialogue_bridge_v01358828.py test_evidence_provenance_v01358826.py
python chat_gui.py
```

## Manual validation
「スファレライトをぐぐって」→ コピーした資料を「クリップ読込」→「なぜカットが難しい？」. Expect an exact excerpt if the copied material explicitly links weak hardness or cleavage to difficult cutting. If it only lists hardness and cleavage separately, expect a **no causal evidence** message instead.
