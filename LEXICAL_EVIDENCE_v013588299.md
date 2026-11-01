# LLM_CHA v0.13.58.82.99 — Lexical Evidence

Goal: reduce false alarms from a tiny 2,286-pair corpus while preserving detection of ungrounded forms. Distinguish Sudachi known terms, out-of-dictionary but corpus-observed terms, protected domain terms, and candidates with neither source. No production model changes.

PowerShell:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.99-lexical-evidence
python -m unittest -v test_lexical_evidence_v013588299.py test_vocabulary_calibrated_v013588298.py
python lexical_evidence_v013588299.py --text "世界点は、あくまでもちが必要。"
python lexical_evidence_v013588299.py --text "スファレライトは閃亜鉛鉱の別名です。" --allow スファレライト --allow 閃亜鉛鉱
```

Categories:
- KNOWN_WORD: recognized by Sudachi regardless of corpus frequency
- CORPUS_ONLY: not in Sudachi dictionary but observed in the pilot corpus index
- SPECIALIZED_TERM: complete phrase explicitly exempted prior to tokenization
- UNKNOWN_COMPOSITION: neither dictionary nor corpus evidence

Caution: Sudachi `is_oov()` depends on tokenization and dictionary coverage. Even KNOWN_WORD is not evidence that a compound is valid or contextually meaningful. `counts` comes from v0.97's frequency>=2 index, not all observed tokens; future work should build all-frequency lexicon and analyze false-positive/false-negative on labeled cases. The implementation is a diagnostic and does not block generation.
