# LLM_CHA v0.2.33.55 — Truth-Aware Semantic Reference Resolution

## Scope
An additional opt-in `/reftruth` command resolves an approved, non-expired Session Reference Memory target through the project's actual `SemanticKnowledgeArchitecture.resolve` facade. It returns knowledge state, Truth State, dispatcher action and a provenance representation. A reference alone is not evidence that the underlying fact is true.

The new bridge conservatively **suppresses answer text** unless the resolved Truth State is explicitly `TRUE`, a usable answer is present, and the knowledge state/action are not unknown or rejected. `FALSE`, `CONTESTED`, `OUTDATED` and `UNVERIFIED` are shown as *review required*. Existing `/refknowledge` remains the raw atomic-proposition lookup (with an unverified warning); `/reftruth` is the policy-aware path.

## Windows PowerShell
```powershell
git fetch origin
git switch v0.2.33.55
git pull origin v0.2.33.55
python -m py_compile chat.py truth_aware_reference_bridge_v023355.py
python -m unittest -v test_truth_aware_reference_bridge_v023355.py test_safe_reference_semantic_bridge_v023354.py
python chat.py --session-reference-memory
```
Once an experiment reference has been explicitly approved, use `/reftruth` for policy-aware retrieval. A missing or unverified match should not yield an invented definition.

## Research boundaries
- No writes to canonical semantic propositions, unified memory, truth records or `/sleep`. 
- No alias inference between a reference label (e.g. `cursor`) and unrelated semantic concepts.
- Provenance is displayed in a conservative string representation, not a formal verified source citation.
- Unit tests include mock SemanticKnowledgeResult-shaped responses; real GPU end-to-end behavior remains unverified until Windows execution.
- Truth State `TRUE` may be manually set, so it is not independent proof of factual correctness. Before production trust, implement stricter evidence quality checks and source verification.
