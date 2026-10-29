# LLM_CHA v0.13.58.82.13 — Wikipedia Topic & Attribute Resolution

## Behavior

When a question reaches the unknown-knowledge Wikipedia fallback, the GUI now separates a **topic** from an **attribute**. Example: `スファレライトの屈折率は？` is resolved to topic `スファレライト` and attribute `屈折率`.

1. Search Wikipedia for the topic, not the whole question.
2. Prioritize one relevant article excerpt for definition/general questions.
3. For recognized attributes (refractive index, chemical composition, hardness, locality), search the retrieved article excerpt for a sentence that explicitly mentions the requested attribute.
4. Return `NO_ATTRIBUTE_EVIDENCE` if an article is found but its retrieved excerpt does not contain that attribute. Do not claim that the missing property has been verified.
5. Retain distinct `NO_HIT` and `ERROR` results.

## Important scope limits

This verifies only that an article excerpt **mentions** the requested attribute; it does not yet establish an unambiguous fact-value relationship, independently validate Wikipedia's truth, or search full article text. Search relevance is heuristic. An article can contain a refractive index somewhere outside the API's introductory excerpt and still yield `NO_ATTRIBUTE_EVIDENCE`. The automatic fallback is GUI-only; the dedicated Wikipedia button remains removed.

The existing Evidence Store, preference dialogue, causal answers, Semantic Memory and model checkpoints are unchanged.

## Windows verification

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.13-wiki-topic-attribute
python -m unittest -v test_wiki_topic_attribute_v013588213.py test_auto_wiki_unknown_v013588212.py
python chat_gui.py
```

Expected interactive scenarios:
- 「量子力学とは？」: if LLM returns 未学習, automatically show the most relevant Wikipedia article excerpt.
- 「スファレライトの屈折率は？」: search by topic and only show attribute evidence if the retrieved excerpt explicitly includes it; otherwise give an evidence-insufficiency message.
- A made-up term: show 未学習 when no relevant article exists.
- No networking: report a search failure without confusing it with a definitive no-hit.
