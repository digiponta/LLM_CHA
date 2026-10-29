# LLM_CHA v0.13.58.82.20 — Unified Episode Context (initial implementation)

A bounded, RAM-only episode record now joins **topic**, **product/subject**, **user-reported action**, and observations over multiple turns. Observations may be annotated with vision, hearing, smell, taste, touch, emotion, and preference dimensions. Multiple dimensions can coexist in the same user utterance; mixed evaluations are retained rather than flattened into a single positive/negative score.

Examples:
- `黒耳を飲んだ` -> start product episode grounded by ProductDialogue.
- `いい香り、少し苦かった` -> two observations, with smell and taste tags, attached to the active product episode.
- `満足` -> emotion observation within the current episode.
- `スファレライトが好きです` -> topic-level preference episode.
- `さっきの感想は？` -> recall the most recent observation set for the active topic.

The user statements are marked `USER_SELF_REPORTED`; they are not verified factual evidence about the product. The model is **not** retrained, no `/sleep` is initiated, and data are not added to persistent Semantic Memory. Maximum of 12 episodes in a running session; no disk persistence. Topic switches do not erase prior episodes, but the GUI's current-topic summary only recalls the most recently recorded episode for that topic.

Current limitations: rule-based wording, not general semantic interpretation; `昨日飲んだコーヒーは香りが良かった` needs richer temporal and subject parsing. The GUI remains the integrated entry point; CLI chat.py is unchanged. A topic-level preference may start a new episode; user identity and external evidence are never inferred from it.

Windows commands:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.20-episodic-context
python -m unittest -v test_episodic_context_v013588220.py test_general_dialogue_intent_v013588219.py test_product_dialogue_v013588217.py
python chat_gui.py
```

Manual dialogue: open the Starbucks page, import clipboard, say `黒耳を飲んだ`, `いい香り、少し苦かった`, `満足`, `さっきの感想は？`. Confirm source excerpts are not rewritten as claims of user experience.
