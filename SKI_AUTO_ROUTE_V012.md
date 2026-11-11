# LLM_CHA v0.12 — Automatic Semantic Query Routing (opt-in)

## Scope

This revision extends the **actual** `chat.py` input loop on top of
v0.11. The existing manual `/ski SOURCE_SD TARGET_SD | ...` command
continues to work.

When enabled, an exact Japanese evidence request such as

```text
主張の根拠を確認してください
主張の根拠は何ですか？
```

can automatically map the source text `主張` to its **unique**
`display_names`-bound native SD ID. It then requires **exactly one**
approved `SUPPORTED_BY` target in the v0.9 converted snapshot.
A fully traceable diagnostic is requested from the SKI Bridge and shown
as `SKI_AUTO_DIAGNOSTIC_ONLY`.

No LLM inference, semantic similarity guesses, fuzzy label matching,
reference-turn guessing, unreviewed predicate auto-mapping, answer
grounding, truth-state change, or learning is performed by this route.
If the request is ambiguous, no native display-name matches, the
allowlisted predicate has zero or multiple targets, or the feature is
disabled, the old LLM_CHA chat route processes the input unchanged.
The original model's Unknown Gate still applies to that old route.

**This is a conservative first stage of natural-language routing,
not a general-purpose natural-language Semantic parser.**

## Windows validation

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch feature/ski-auto-router-v0.12
git pull --ff-only
python -m unittest -v test_ski_runtime_v011.py test_ski_auto_route_v012.py

cd C:\Users\inoma\git\misc\LLM_SKI_BRIDGE
git fetch origin
git switch feature/cha-auto-router-v0.12
git pull --ff-only
python -m unittest discover -s tests -v
python verify_cha_auto_route_v012.py `
  --llm-cha-dir C:\Users\inoma\git\misc\LLM_CHA `
  --llm-tmp-dir C:\Users\inoma\git\misc\LLM_TMP
```

The LLM_CHA tests are 12 existing v0.11 plus 15 new (expected 27).
SKI Bridge retains 98 tests. The new integration verification
checks two positive Japanese utterances, four pass-through conditions,
disabled mode and source immutability (eight checks total).

## Start actual LLM_CHA with the synthetic registry

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
$env:LLM_CHA_SKI_ENABLED="1"
$env:LLM_CHA_SKI_AUTO_ENABLED="1"
$env:LLM_CHA_SKI_BRIDGE_DIR="C:\Users\inoma\git\misc\LLM_SKI_BRIDGE"
$env:LLM_CHA_SKI_TMP_DIR="C:\Users\inoma\git\misc\LLM_TMP"
$env:LLM_CHA_SKI_NATIVE="C:\Users\inoma\git\misc\LLM_SKI_BRIDGE\examples\llm_tmp_native_registry_v09.json"
$env:LLM_CHA_SKI_PREDICATE="support-pred"
python chat.py
```

At the real `You>` prompt, type:

```text
主張の根拠を確認してください
```

Expected diagnostic: `ski_auto_status=FOUND`, displayed with
`【SKI自動照会・事実未検証】`. An unrelated normal chat input is still
processed by LLM_CHA; `/ski` remains manually usable.

Disable autonomous routing only:

```powershell
Remove-Item Env:\LLM_CHA_SKI_AUTO_ENABLED -ErrorAction SilentlyContinue
```

## Boundaries

Native SD `APPROVED` is an **unverified stored label** and the
`support-pred` mapping is synthetic for this example. The returned
diagnostic is **not a factual answer**; user review, provenance
authentication, real semantic intent disambiguation, and model
answer integration are separate subsequent work.
