# LLM_CHA v0.3.6.5 — Active Grounded Revisit and Cursor Hygiene

Experimental branch `v0.3.0`; stable `main` and `v0.2.34` remain unchanged.

The Active-only conversation adapter now rewrites an explicit bare topic question such as `宇宙について` to `宇宙について教えて`. The existing Truth Gate / Corpus retrieval still determines what may be said. Default and Shadow routing remain unchanged.

When Active retention has removed or expired a topic, its *transient presented-proposition cursor* entry is discarded before the Truth Gate processes another turn. Re-admitting the topic starts pagination fresh; it does not restore remembered facts or silently bypass knowledge validation. This is a chosen Active-context semantic, and needs GPU validation against corpus changes and ground truth.

## Local verification

```powershell
git switch v0.3.0
git pull --ff-only origin v0.3.0
python -m unittest -v test_grounded_revisit_v0365.py
python -m unittest -v test_active_topic_context_v0363.py test_active_retention_gpu_accept_v0364.py
python active_retention_gpu_accept_v0364.py --timeout 240
python verify_integration_v0362.py --gpu --legacy --timeout 240
```

Existing 233-case integrated gate and 21 Active-mode tests are unchanged. This adds **8 further unit cases**, giving 262 distinct cases when counted across these separate suites (233 + 21 + 8), not yet one unified runner. This release remains experimental. Active + Context Recovery stays deliberately blocked until a separately reviewed restore bridge exists.

## Next

Expand the GPU harness with an explicit `宇宙について` grounded-retrieval fixture and a policy-evicted then re-admitted topic, verifying that the cursor restarts without stale information or unauthorized generation. Check that the more general `Xについて` phrasing is sufficiently precise before promoting beyond Active mode.
