# LLM_CHA v0.13 — Multi-Turn SKI Context Diagnostics

This branch extends the live `chat.py` input loop and the existing v0.11/
v0.12 SKI integration.

## Implemented scope

- An **opt-in, session-local context pointer** retains a single explicitly
  mentioned native SD source ID. No text/evidence is added to model prompts.
- It recognizes narrow Japanese follow-ups such as `その根拠は？` or
  `根拠は？` when the prior topic is unique and has exactly one
  APPROVED, explicitly mapped `SUPPORTED_BY` target.
- A follow-up may have at most one intervening ordinary chat input (two
  turn gaps from the original mention). Longer gaps expire the context.
- Explicit competing topics clear the pointer. A different unmapped topic
  also clears it. `/reset` clears it without changing the original reset
  implementation.
- The actual LLM_TMP `context_intent_resolver_v033.py` is loaded and its
  `MULTIPLE_TOPICS`/`MULTIPLE_ATTRIBUTES` abstention is honored as a
  **secondary ambiguity veto**. Its fixed TOPICS/attributes cannot
  recognize all native Registry subjects and are *not* silently used as
  factual evidence; the native SD display-name match remains the source
  resolver.
- Ordinary unrelated input and unrecognized short references fall through
  to the original LLM_CHA normal chat flow.
- Successful matches call the existing v0.11 SKI and v0.7 Truth Boundary
  diagnostic. No SKI-derived fact is inserted into the model context,
  answer text, truth state or training dataset.

This is **bounded context reference routing**, not a full general-purpose
LLM-driven semantic parser or verified factual answer generator.

## Local Windows tests

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch feature/ski-context-v0.13
git pull --ff-only

python -m unittest -v `
  test_ski_runtime_v011.py `
  test_ski_auto_route_v012.py `
  test_ski_context_route_v013.py

cd C:\Users\inoma\git\misc\LLM_SKI_BRIDGE
git fetch origin
git switch feature/cha-context-v0.13
git pull --ff-only

python -m unittest discover -s tests -v

python verify_cha_context_v013.py `
  --llm-cha-dir C:\Users\inoma\git\misc\LLM_CHA `
  --llm-tmp-dir C:\Users\inoma\git\misc\LLM_TMP
```

Expected: LLM_CHA 46 focused tests (12 + 15 + 19),
SKI Bridge 102 tests (previous 100 + 2 new), and the three-repository
multi-turn verifier 14 scenarios. These numbers are expected test counts,
not claims of local execution.

## Actual chat.py session with synthetic native snapshot

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
$env:LLM_CHA_SKI_ENABLED="1"
$env:LLM_CHA_SKI_AUTO_ENABLED="1"
$env:LLM_CHA_SKI_CONTEXT_ENABLED="1"
$env:LLM_CHA_SKI_BRIDGE_DIR="C:\Users\inoma\git\misc\LLM_SKI_BRIDGE"
$env:LLM_CHA_SKI_TMP_DIR="C:\Users\inoma\git\misc\LLM_TMP"
$env:LLM_CHA_SKI_NATIVE="C:\Users\inoma\git\misc\LLM_SKI_BRIDGE\examples\llm_tmp_native_registry_v09.json"
$env:LLM_CHA_SKI_PREDICATE="support-pred"
python chat.py
```

Enter two consecutive turns:

```text
主張について教えて
その根拠は？
```

The first line is handled by the original LLM_CHA engine, possibly
answering `未学習です`. Its explicit SD topic is remembered separately
for SKI only. The second should show an unverified
`ski_context_status=FOUND` diagnostic from the synthetic snapshot.
The diagnostic is **not** a model-generated factual answer.

To explicitly erase SKI and regular conversation state, use `/reset`.
To disable context routing while preserving single-turn v0.12 routing:

```powershell
Remove-Item Env:\LLM_CHA_SKI_CONTEXT_ENABLED -ErrorAction SilentlyContinue
```

## Safety limitations

The sample data has only `CLAIM`, `EVIDENCE`, and `OTHER` SD IDs and
is synthetic. No real user's medical/mineral/other facts or authenticity
of evidence have been evaluated. A native APPROVED relation is still
`approval_authenticated=false`, `verified_fact=false`.
The LLM_TMP v0.33 resolver is used as a narrowly defined conservative
ambiguity check, *not* as a complete language or truth resolver.
