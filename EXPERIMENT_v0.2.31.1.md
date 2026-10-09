# LLM_CHA v0.2.31.1 — Purpose Confidence & Confirmation

Implemented as a separate deterministic controller. Windows unit tests and runtime dialogue evaluation are pending.

v0.2.31.0 demonstrated clarification then goal handoff in a controlled conversation. This version adds heuristic confidence (not a calibrated probability), CONFIRMING state, yes/no correction, basic negation and explicit goal switching.

The purpose controller asks one clarification per turn only when needed. A clear request skips confirmation. CONFIRMING asks a yes/no question for an ambiguous request such as Pythonを試したい. A negative answer returns to DISCOVERING. A broad AI development goal requests a target such as LLM or image recognition.

Limitations: keyword rules do not provide general semantic intent understanding. This implementation does not call the LLM generator or calibrate probability. HANDOFF acknowledges an identified goal only. Future experiments should add held-out paraphrases, robust negatives and compare unnecessary clarification rates.

## Commands

    git fetch origin
    git switch v0.2.31.1
    git pull origin v0.2.31.1
    python -m unittest -v test_purpose_confidence_v02311.py
    python purpose_confidence_v02311.py

Try: Pythonを試したい → いいえ → 勉強したい → やっぱり画像認識を作りたい
Use /state, /reset and /quit in the interactive shell.