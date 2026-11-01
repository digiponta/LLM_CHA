# v0.13.58.82.98: Vocabulary calibration

Results from v0.97: 4/4 tests passed; 4,963 observed Sudachi types, 2,543 with frequency >=2. The output marked legitimate word あくまで as unknown and missed the unnatural expression 世界点; the specialist exemption 閃亜鉛鉱 did not protect its split constituents.

This revision uses SudachiPy Dictionary.tokenizer() (non-deprecated), protects exact allowed phrases **before** morphological segmentation, and labels unobserved forms OUT_OF_CORPUS_REVIEW rather than asserting invented words. It is a diagnostic tool, not a model generation restriction.

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.98-vocabulary-calibration
python -m unittest -v test_vocabulary_calibrated_v013588298.py test_vocabulary_grounded_v013588297.py
python audit_vocabulary_calibrated_v013588298.py --text "世界点は、あくまでもちが必要。"
python audit_vocabulary_calibrated_v013588298.py --text "スファレライトは閃亜鉛鉱の別名です。" --allow スファレライト --allow 閃亜鉛鉱
```

Use an independent, appropriately licensed larger Japanese lexicon and held-out naturally occurring responses to estimate false-positive rates before considering rejection at runtime. Even ordinary dictionary coverage does not ensure that a term is used in a sensible compound, and positive vocabulary coverage does not show question-answer relevance. No training, production model replacement, or `chat.py` changes are performed.
