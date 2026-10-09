# LLM_CHA v0.2.31.4 — Semantic Purpose Estimator Experiment

Implemented as a diagnostic *vector similarity baseline*, **not** the existing LLM_SEM semantic encoder. No new synonym rewrite rules and no LLM_CHA model training.

## Motivation
v0.2.31.3 got 24/24 on previously inspected development examples, but 6/12 on a fresh test set. Test whether similarity among example sentences generalizes beyond literal normalizer rules.

## Method
The estimator learns corpus-derived character 2–4-gram IDF weights from 32 labelled examples across learning, development, troubleshooting and casual purposes. Cosine similarity to the nearest purpose-labelled exemplar determines candidates. Abstain if highest similarity is below threshold or its margin below the runner-up. Similarity is **not a calibrated confidence**. No handwritten text substitution/synonym dictionary is involved. Nonetheless character n-grams are lexical, not proven semantic understanding.

Compare baseline v0.2.31.1, normalized v0.2.31.3, and new vector similarity method on:
- previously_seen_v02312 (24 records, previously inspected),
- previously_seen_v02313 (12 records, previously inspected),
- prospective_v02314 (15 manually authored new records).

Important: goal-only classification is evaluated here. A null prediction is interpreted as abstention. This is not a full five-state dialogue evaluation. The 15 new examples are small and related to example corpus terms, so do not claim wide open-domain generalization. Leave this set untouched until results have been examined.

## Windows
```powershell
git fetch origin
git switch v0.2.31.4
git pull origin v0.2.31.4
python -m unittest -v test_semantic_purpose_v02314.py
python evaluate_semantic_purpose_v02314.py
```

## Next
If the baseline is promising, build an adapter using an actual available LLM_SEM encoder and compare it with identical frozen datasets and splits. Also evaluate ambiguity, negation and multi-turn goal changes before integration into DSS. If abstentions or misclassifications dominate, improve the purpose-labelled representations and evaluation design instead of automatically adding rules.