# LLM_CHA v0.1.0 — Character Selection Integration

Implementation on branch `v0.1.0`.

## Commands

```powershell
python chat.py --character nagato
# or launch with no profile, then in interactive prompt:
/character list
/character select nagato
/character show
/character off
```

Custom JSON profiles live under `characters/ID.json`; specify `--character-dir PATH` to change this directory.

A character profile contains `profile_id`, `display_name`, `persona`, `speaking_style`. No profile is active by default. When active, the reply display label changes from `AI>` to the profile's display name.

## Isolation guarantee (scope)

- Character selection does not modify the incoming user query or semantic routing.
- It does not write to Semantic Memory, the teaching queue, checkpoint, or `/sleep` state.
- Existing truth gates, conditional retrieval and unknown rejection remain responsible for answer content.
- `persona` and `speaking_style` are currently metadata only. A future release may style *approved conversational responses* after semantic verification, with a dedicated no-factual-drift regression.
- A profile label is a presentation setting; it does not imply that the model is fully trained to imitate the named character.

## Tests

```powershell
python -m unittest -v test_character_profile_v010.py test_character_runtime_v010.py
python verify_semantic_sleep_v10131.py
python verify_conditional_runtime_stable_v10165.py
```

The first command uses the Python standard library only. The remaining legacy commands may require model/data files or additional dependencies.

**Verification status:** code committed; full local CPU/GPU regressions not executed by the GitHub integration. Keep branch separate from `main` until tests pass.
