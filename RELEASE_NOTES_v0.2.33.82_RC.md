# LLM_CHA v0.2.33.82 — Stable Candidate Release Notes

**Release phase:** Stable Candidate (RC), not official Stable Release.
**Source branch:** `v0.2.33.82-multitopic-context`
**Candidate branch:** `v0.2.33.82-stable-candidate`
**Base main:** `95424d7e358b0c1d989c87d225dcbfba8d675072`.

## Implemented milestones

| Revision | Scope |
|---|---|
| .1 | Transient Multi-Topic Context, TTL, ambiguous-reference and reset guards |
| .2 | Conversation Topic Adapter |
| .3 | Multi-Topic Runtime Injection shell |
| .4/.4.1 | Opt-in integration in chat.py and learning-state regression fix |
| .5 | Grounded follow-up: avoids unconstrained generation |
| .6 | Non-repetitive proposition paging / context reset |
| .7 | Proposition-level IDs, read-only Truth Overlay and provenance |
| .8 | Human-operated JSONL review workflow and mixed-state tests |
| .9 | Deterministic fixture-only mixed-state component E2E tests |
| .10 | Real GPU chat.py smoke runner, temporary corpus snapshot and overlay |

## Verified evidence (Windows PowerShell / CUDA RTX 3070 Ti)

- v0.2.33.82.9: 90/90 cumulative regression tests PASS, user-supplied log.
- v0.2.33.82.10: 4/4 additional acceptance harness tests PASS.
- **94 cumulative component/regression tests pass across those executions**; one fresh combined 94-test run has not yet been logged.
- v0.2.33.82.10: real chat.py GPU subprocess **8/8 acceptance checks PASS**, returncode 0, from user-supplied `mixed_state_gpu_accept_v02338210.json`.
- Observed simulated states: FALSE blocked, TRUE displayed, UNVERIFIED labeled, OUTDATED and CONTESTED blocked; `/reset` asks for a topic; temporary corpus copy unchanged.

## Preservation and limitations

- All tested review states are **synthetic filtering fixtures**, not independent assessment of the correctness of cosmic/physical claims.
- The model outputs for grounded follow-up were retrieval-based (0 probe tokens); this does not imply that the SFT model weights incorporated this memory.
- Overlay is read-only in chat; review CLI is explicit, requires ID/evidence/reviewer/reason, denies conflicting state updates. It does not itself verify evidence.
- Only the corpus copy and proposition overlay are isolated in the GPU smoke runner; additional chat startup/configuration artifacts might access ordinary project data.
- No merge to `main` or GitHub Release/tag was performed in this stage.
- Repository README historically starts with LLM_TRY v10.16.5; RC update adds a new LLM_CHA section while preserving original history.

## Pre-release checklist

- [x] Preserve development branch; create separate stable-candidate branch
- [x] Document history, feature flags, architecture and observed test evidence
- [x] Document unverified truth, limited isolation and current branch differences
- [ ] Run all 94 tests **in a single invocation** on the candidate branch
- [ ] Run GPU acceptance on candidate branch and archive JSON report
- [ ] Evaluate baseline LLM_TRY legacy regressions where applicable
- [ ] Confirm local working-tree state and readme/doc consistency
- [ ] Only then decide merge into main and tag/release

## Reproduction

```powershell
git fetch origin
git switch v0.2.33.82-stable-candidate
git pull --ff-only origin v0.2.33.82-stable-candidate
python -m unittest -v test_multi_topic_context_v0233821.py test_conversation_topic_adapter_v0233822.py test_multi_topic_chat_runtime_v0233823.py test_truth_aware_chat_integration_v0233824.py test_learning_init_v02338241.py test_grounded_followup_v0233825.py test_grounded_expansion_v0233826.py test_expansion_integration_v0233826.py test_proposition_truth_v0233827.py test_truth_integration_v0233827.py test_proposition_review_v0233828.py test_mixed_state_e2e_v0233829.py test_mixed_state_gpu_accept_v02338210.py
python mixed_state_gpu_accept_v02338210.py --timeout 240
```
