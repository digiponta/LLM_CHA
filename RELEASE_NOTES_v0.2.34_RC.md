# LLM_CHA v0.2.34 — Stable Candidate (not released)

Branch: `v0.2.34-stable-candidate`
Source: `v0.2.34-longterm-context`
Stable previous version: `v0.2.33.82` (unchanged).

## Completed implementation
- v0.2.34.0 checkpoint for bounded topic and proposition ID history.
- v0.2.34.1 restore-time current-corpus and Truth State revalidation.
- v0.2.34.2 real subject-keyed corpus adapter using the existing retrieval and Truth Gate conventions.
- v0.2.34.3 opt-in `chat.py` commands `/context-save` / `/context-load`.
- v0.2.34.4 multi-process GPU acceptance harness for restore and synthetic OUTDATED revocation.
- v0.2.34.5 atomic checkpoint replacement, max-size guard, multi-topic and failed-write regression tests.

## Evidence already supplied by the developer (Windows RTX 3070 Ti)
- New 47/47 unit regressions PASS in one invocation.
- GPU restart/revocation: 14/14 checks PASS, three child processes exit 0.
- LLM_TRY v10.16.5: 48 historical cases PASS; stable integration 6/6 PASS.

**Not yet shown on this candidate branch:** legacy 94 LLM_CHA tests; a single combined run of all 141; an updated GPU acceptance run on the candidate branch. Do not merge or tag based on prior evidence alone.

## Acceptance command

```powershell
git fetch origin
git switch --track origin/v0.2.34-stable-candidate
python verify_release_candidate_v02334.py --gpu --legacy
```

The verifier runs 141 unittest cases in **one invocation** (94 baseline + 47 new), checks the exact expected total, then runs v0.2.34.4 GPU acceptance and legacy conditional verification. A failure returns nonzero and prints `RELEASE_GATE_V02334_FAIL`; all checks succeeding prints `RELEASE_GATE_V02334_PASS`.

If already checked out locally, use `git switch v0.2.34-stable-candidate` and `git pull --ff-only origin v0.2.34-stable-candidate`.

## Known limitations
- Checkpoint contains topic names and proposition IDs; protect its filesystem permissions.
- Truth labels for the GPU revocation fixture are synthetic; they do not scientifically validate facts.
- GPU harness isolates corpus copy, overlay and checkpoint but not all other runtime support artifacts.
- Atomic replace does not prove crash-safe power-loss durability or transactional reads during concurrent corpus mutation.
- The opt-in interface is disabled unless explicitly enabled. `main` and v0.2.33.82 tag remain unchanged.
