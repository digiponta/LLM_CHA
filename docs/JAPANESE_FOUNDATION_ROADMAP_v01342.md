# LLM_CHA v0.13.42 — Japanese Foundation First

## Policy change
Primary objective: establish coherent Japanese sentence generation **before** optimizing multi-turn RPC conversation, persona or response ranking. This is a research plan; no training performance is claimed.

## Existing baseline (freeze)
- Preserve the 100K RPC candidate and all v0.13.39–v0.13.41 reports without overwriting.
- Do not consume reserved RPC test split.
- Do not automatically promote external facts or AI-reviewed labels into approved Semantic Memory.

## Stages and promotion gates
1. **Foundation corpus audit**: inspect available Japanese foundation prose, literary and conversational material. Deduplicate, remove corrupted strings and ill-formed sentence boundaries, separate by source/work/document into train and *source-independent* validation splits. Audit licenses and data provenance before training. Prevent contamination with eval prompts.
2. **Continuation baseline**: measure unconditional/short-prefix continuation fluency, syntactic coherence, repetition, EOS termination and topical consistency of the frozen base and 100K RPC models. Run reproducible seeds; blind human assessment for subjective criteria.
3. **Japanese foundation adaptation**: train an experimental checkpoint on clean Japanese prose with the same tokenizer/architecture initially, compare from-base vs from-100K starts. Use held-out perplexity and human sentence-quality metrics. Save checkpoints under new names. Mix a small stable conversational replay set only if necessary to limit catastrophic forgetting.
4. **Instruction / question-answer stage**: controlled Japanese QA tasks, explicitly distinguish statements/questions and speaker intent. Require topical consistency and evidence gating.
5. **Multi-turn RPC adaptation**: only after foundation gates pass, resume RPC learning and multi-turn context tests. Compare v0.13.39 conditional NLL and v0.13.41 quality on untouched development probes, and keep true test split sealed.

## First experiment v0.13.42
Diagnostic-only prefix continuation comparison (not training):
- Source: independent, clean Japanese validation sentences, not the training set.
- Prefix lengths: 0, 4, 12, 24 BPE tokens where possible.
- Compare candidate-free continuation with fixed seeds and greedy, score grammar, coherent completion, topic drift, token repetition and exact EOS.
- Teacher-forced NLL and free-running assessments reported separately.
- Record source licensing, dataset fingerprints and tokenizer / checkpoint SHA.
- Do not claim the model can generate natural Japanese solely from a falling NLL.

## Decision rules
- If clean prose continuation is poor even with 12+ ground-truth tokens, prioritize language modeling / architecture / corpus.
- If long ground-truth prefixes produce fluent continuations while zero/short prefixes fail, prioritize response initiation and conditioning.
- If foundation continuation improves but RPC degrades, adjust mixed replay and stage curriculum.
- If fluent single-turn output exists yet dialogue response relevance fails, then add Semantic Response Planning / relevance ranker.

## Evaluation governance
AI-assisted reviews must be explicitly labeled AI_AUDIT_COMPLETED and cannot be reported as HUMAN_AUDIT_COMPLETED. Human review is separately attested. Show sample sizes, limitations and paired comparisons.
