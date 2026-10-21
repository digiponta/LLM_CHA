# LLM_CHA v0.6.3 — Semantic Natural Language References

This change extends the **experimental conversation candidate** memory, not
the model checkpoint or the separate long-term Semantic Memory implementation.

## Data model

Each candidate proposition retains `source_turn`, `source_text`, and a
`natural_language_refs` list. Each source ref has `text_id`, `language`,
`relation=source`, `uri`, `version=1`, and `content_hash`.

Conversation state includes `natural_language_texts` keyed by logical
`nl://` URI. Each entry contains its exact original utterance and hash.
These logical URIs are resolved by the local Python resolver only. They are
not external HTTP endpoints and are not yet SKI wire-protocol messages.

## Design boundaries

- `relation=source` means *evidence text*, not canonical semantic equivalence.
- Text may be subjective, false, incomplete, or sensitive. No promotion,
  verification, training, or model update occurs.
- `sha256` protects against accidental mismatch, not an attacker who can
  change both the text and its hash.
- Only detected candidate propositions receive text references. Other
  dialogue turns still use the preexisting conversation history.
- Old saved states can be read; `validate` adds references in its returned
  copy. Saving through `save_atomic` persists the upgraded representation.
- Vectors remain local to the source model; no vector interchange is added.
- Future SKI transport must embed text when its `nl://` logical URI cannot
  be resolved by the receiver, and preserve source IDs and provenance.

## Verification

```powershell
python -m unittest -v test_semantic_natural_language_refs_v063.py test_incremental_semantic_memory_v042859.py test_conversation_semantic_memory_v042857.py
```

## Example

```python
from conversation_semantic_memory_v042857 import new_memory
from incremental_semantic_memory_v042859 import append
from semantic_natural_language_refs_v063 import resolve_natural_language

memory = new_memory("demo")
append(memory, "user", "私は車を持っていない")
reference = memory["propositions"][0]["natural_language_refs"][0]
print(reference["uri"])
print(resolve_natural_language(memory, reference["uri"]))
```
