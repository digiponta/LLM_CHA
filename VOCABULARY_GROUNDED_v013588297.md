# LLM_CHA v0.13.58.82.97 Vocabulary Grounding — audit phase

Purpose: suppress invented Japanese words without requiring every sentence to be copied from training text. This first version **audits** morphological words in generated answers; it does **not** alter chat.py, model weights, token logits, or the runtime response gate. Corpus-only dictionary coverage is not a correctness guarantee.

Windows:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.97-vocabulary-guard
python -m unittest -v test_vocabulary_grounded_v013588297.py
python -m pip install sudachipy sudachidict_core
python build_vocabulary_index_v013588297.py --input data/real_persona_pilot_v013588293.jsonl
python vocabulary_grounded_decoder_v013588297.py --text "世界点は、あくまでもちが必要。"
python vocabulary_grounded_decoder_v013588297.py --text "スファレライトは閃亜鉛鉱の別名です。" --allow スファレライト --allow 閃亜鉛鉱
```
Reports REVIEW for any token not observed at least twice in the selected corpus (unless exempted); IN_VOCABULARY means lexical coverage only, **not** that the wording is meaningful or responsive. False positives are likely for inflections, rare legitimate terms and proper names. The user can inspect the JSON dictionary locally. A training-set-only lexicon is narrow; broaden with independently licensed Japanese text only after provenance and privacy review. Next: compare hallucinated-token detection on held-out real vs malformed responses before enabling any hard token-level restrictions. The implementation uses SudachiPy morphological surfaces, not BPE IDs, to avoid mistaking subword tokens for words.
