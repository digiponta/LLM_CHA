# LLM_CHA v0.2.33.49 — Natural-Language Confirmation & Reference Lifecycle

An **experimental** `GuardedConfirmationBridge` subclasses the current contextual policy. It only accepts strictly whitelisted Japanese/English yes/no replies **while a candidate is pending in the same context**. A plain yes without such a candidate cannot approve anything. Qualified, negated and ambiguous assent is left to the resolver's `confirm_required` behavior, not guessed. All candidate mutations still flow through the existing `confirm(True/False)` API. The project chat.py and production Semantic Memory are untouched.

Scenarios: affirmative approval, explicit rejection, ambiguous/negated assent, missing pending confirmation, interruption after candidate, cancellation, rejection/retry, conversation-context separation.

## PowerShell
```powershell
git fetch origin
git switch v0.2.33.49
git pull origin v0.2.33.49
python -m py_compile natural_confirmation_lifecycle_v023349.py
python -m unittest -v test_natural_confirmation_lifecycle_v023349.py test_e2e_dialogue_resolution_v023348.py
python natural_confirmation_lifecycle_v023349.py
```
Output `results/natural_confirmation_lifecycle_v023349.json`. Script refuses overwrite.

## Important research limitations

This is a narrow exact-phrase rule, not comprehensive language understanding. The test cases are developer-authored and not independent. The experimental file does **not yet exercise fake-clock expiration**: clock-controlled candidate TTL and pending-turn TTL need separate explicit tests before any claim of expiry safety. Integrating to the actual user-facing chat runtime and Semantic Memory remains future work. Record provenance, context isolation, and explicit approval must remain invariant.
