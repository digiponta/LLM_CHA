# LLM_CHA v0.2.31.0 — Purpose Discovery Dialogue

Prototype implemented independently of the LLM_CHA language model.
This is deterministic dialogue policy plus Dialogue Semantic State (DSS),
not a trained model and not a proof of generalized intent understanding.

## Why
v0.2.30.1 improved some first-topic mentions, but topic continuation
and v0.2.30.4 recovery free generation remained weak. v0.2.30.5
demonstrated lower teacher-forced target NLL without topical free responses.
The new approach separates *deciding what to do in conversation* from
*generating a fluent response*.

## State model
UNKNOWN -> DISCOVERING -> READY -> EXECUTING (CONFIRMING reserved for a
future explicit confirmation policy). Purpose candidates: learning,
development, troubleshooting, casual. Keeps topic, purpose, missing
information, candidates, last question, and turns in DSS. Goal switches
override the former purpose. An unknown goal results in one clarification
question per turn; casual conversation is a valid goal.

For this first prototype, Purpose Estimator is keyword/phrase-based;
Dialogue Policy replies with fixed Japanese templates. HANDOFF means the
goal is recognized and could be passed to an external planner or the
LLM_CHA generator in a later integration. No LLM generation is performed
by this script; recognizing the topic is not equivalent to answering well.

## Windows commands
\`\`\`powershell
git fetch origin
git switch v0.2.31.0
git pull origin v0.2.31.0
python -m unittest -v test_purpose_discovery_v02310.py
python purpose_discovery_v02310.py
\`\`\`

Try:
- 最近、Pythonを触っているんだけど
- AIを作りたい
- 小さなLLMを自作したい
- /state
- やっぱり画像認識を作りたい
- 少し雑談したい
- /reset

## Limitations and next steps
- Keyword rules do not cover open-domain goal inference, negation,
  uncertainty, or nuanced Japanese dialogue.
- CONFIRMING is specified but not yet reached: add uncertainty/
  confirmation handling after controlled evaluation.
- Goal discovery can ask redundant or awkward questions on some
  paraphrases; add heldout paraphrase tests.
- Compare unnecessary question rate, number of turns to goal discovery,
  correct goal switching, and response relevance against the current
  base chat system.
- Only after this deterministic baseline works should its state and
  HANDOFF be connected to Semantic Memory / LLM_SEM and the LLM_CHA
  text generator.
