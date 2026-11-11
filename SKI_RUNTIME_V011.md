# LLM_CHA v0.11 — SKI Real Runtime Hook (opt-in)

This branch modifies the **actual LLM_CHA `chat.py` input loop**:
before any semantic retrieval, RSE, model generation, or learning path,
an explicit `/ski SOURCE_SD TARGET_SD | question` command is consumed by
`ski_runtime_v011.py`. No other user input is changed.

The hook dynamically uses the trusted local sibling repositories:
- `LLM_SKI_BRIDGE` branch `feature/cha-runtime-contract-v0.11` (inherits v0.10)
- `LLM_TMP` with `intent_sd_context_v03.py` and
  `semantic_relation_graph_v035.py`.

The command reads the native Intent SD frozen JSON snapshot and optionally
maps one explicitly allowlisted predicate SD ID to `SUPPORTED_BY`.
All native approvals are **unauthenticated relation labels**.
It performs the SKI v0.5 A / ACK / B roundtrip and v0.7 Truth Boundary.
Only a **diagnostic** is displayed; relation content is not fed to the
LLM, learned, stored, or promoted to factual truth.

**Important scope:** This is a real in-process call from `chat.py`
to the LLM_TMP graph implementation, NOT answer generation based on SKI.
Autonomous intent-to-SD matching, model-generated SKI-grounded answers,
real user-review provenance verification and production transport remain
separate future stages. The original Truth Gate is not bypassed.

## Windows verification

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch feature/ski-runtime-integration-v0.11
git pull --ff-only
python -m unittest -v test_ski_runtime_v011.py

cd C:\Users\inoma\git\misc\LLM_SKI_BRIDGE
git fetch origin
git switch feature/cha-runtime-contract-v0.11
git pull --ff-only
python -m unittest discover -s tests -v
python verify_cha_runtime_hook_v011.py `
  --llm-cha-dir C:\Users\inoma\git\misc\LLM_CHA `
  --llm-tmp-dir C:\Users\inoma\git\misc\LLM_TMP
```

## Run actual chat.py (requires local model dependencies and checkpoints)

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
$env:LLM_CHA_SKI_ENABLED="1"
$env:LLM_CHA_SKI_BRIDGE_DIR="C:\Users\inoma\git\misc\LLM_SKI_BRIDGE"
$env:LLM_CHA_SKI_TMP_DIR="C:\Users\inoma\git\misc\LLM_TMP"
$env:LLM_CHA_SKI_NATIVE="C:\Users\inoma\git\misc\LLM_SKI_BRIDGE\examples\llm_tmp_native_registry_v09.json"

# Safest default: NO predicate mapping.
Remove-Item Env:\LLM_CHA_SKI_PREDICATE -ErrorAction SilentlyContinue
python chat.py
```

At `You>`:

```text
/ski CLAIM EVIDENCE | 関係の確認
```

This should display `ski_status=NOT_FOUND`. For the **synthetic** sample
only, set `$env:LLM_CHA_SKI_PREDICATE="support-pred"` **before** starting
`chat.py` to see `ski_status=FOUND` for the same request.
`/ski CLAIM MISSING | 状態確認` should return `UNKNOWN_NODE`.

The command never changes LLM_CHA learning state, model context,
truth overlay or the snapshot file. Without
`LLM_CHA_SKI_ENABLED=1`, it returns `DISABLED` and does not load
sibling modules. Bad format and missing files return a fail-closed
`ERROR` diagnostic rather than falling through to the model.

To disable again:

```powershell
Remove-Item Env:\LLM_CHA_SKI_ENABLED -ErrorAction SilentlyContinue
```

**Do not use an arbitrary native file without reviewing its origin.**
The local source directory parameters import Python code and must refer
only to trusted checkout paths. Local APPROVED tags alone are not an
authority for model usage or truth promotion.
