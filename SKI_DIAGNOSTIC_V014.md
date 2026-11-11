# LLM_CHA v0.14 — SKI Diagnostic Response in Dataset B

The v0.13 live chat.py SKI integration remains intact. The new v0.14
SKI Bridge provides a structured `diagnostic` object inside SKI
Natural-Language **Dataset B**. The runtime adapter
`ski_runtime_v011.execute_ski_query` now REQUIRES and validates that
structured SKI profile after running `assess_exchange` and before
displaying the diagnostic. The returned local decision is not a second
SKI response.

**SKI v0.5 Dataset A/B/ACK remains the underlying message format.**
The diagnostic is an experimental optional metadata profile rather than
a change to canonical HASKI_DOC v0.5 framing.

The v0.14 field binds the Dataset A message ID, evidence request and
response IDs, source/target SD IDs, search status, bounded path length,
truth/approval state and the all-false policy flags. No raw source
evidence text or untrusted provenance is placed into the diagnostic.

The local LLM_CHA display now includes
`ski_profile=ski-diagnostic-v0.14` when a validated profiled SKI
Dataset B response was consumed.

## Windows validation

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch feature/ski-diagnostic-v0.14
git pull --ff-only

python -m unittest -v `
  test_ski_runtime_v011.py `
  test_ski_auto_route_v012.py `
  test_ski_context_route_v013.py `
  test_ski_diagnostic_v014.py

cd C:\Users\inoma\git\misc\LLM_SKI_BRIDGE
git fetch origin
git switch feature/ski-diagnostic-v0.14
git pull --ff-only
python -m unittest discover -s tests -v

python verify_ski_diagnostic_v014.py `
  --llm-cha-dir C:\Users\inoma\git\misc\LLM_CHA `
  --llm-tmp-dir C:\Users\inoma\git\misc\LLM_TMP

python verify_cha_context_v013.py `
  --llm-cha-dir C:\Users\inoma\git\misc\LLM_CHA `
  --llm-tmp-dir C:\Users\inoma\git\misc\LLM_TMP
```

Expected tests: LLM_CHA **53** focused (49+4),
SKI Bridge **122** (105+17). The dedicated v0.14 verifier has
**9 checks**, with a separate v0.13 **14-check** compatibility suite.
These are expected, not yet observed post-change Windows results.

## Real chat.py demonstration (synthetic snapshot)

With the same LLM_CHA SKI environment configuration in
`SKI_CONTEXT_V013.md`, run `python chat.py` and enter:

```text
主張について教えて
その根拠は？
```

The expected response footer is:

```text
[ski_context_status=FOUND, route=SKI_CONTEXT_DIAGNOSTIC_ONLY, ski_profile=ski-diagnostic-v0.14]
```

This means the diagnostic reached LLM_CHA **as part of a structured SKI
Dataset B**, passed receiver-side structural validation, and was
displayed as an explicitly unverified diagnostic. It does **not** mean
that any fact has been independently verified, that the data source is
authenticated, or that the LLM has used the evidence for generation.

A v0.14 runtime paired with an older v0.13 Bridge (without the
diagnostic) will fail closed with a diagnostic error. This is an
intentional runtime profile requirement. The v0.14 Bridge's
`assess_exchange` itself still accepts legacy messages.

The synthetic fixture is not a production registry. There is no real
network service or distributed execution: the current SKI roundtrip
is between local Python modules.
