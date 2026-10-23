# LLM_CHA v0.7.11 — Trusted Runtime UNKNOWN → Experimental Quality-Gated Fallback

Production `chat.py` integration is **explicitly opt-in**, preserving all
existing Trusted routes, Approved QA overlay, Semantic Memory, contextual
evidence, and Wikipedia routing. Only when the existing dispatch sets
`resolution_name == "UNKNOWN_KNOWLEDGE"` does the Experimental Adapter run.
The fallback is intentionally **not attempted** for `TRUTH_BLOCK` or
`INTERNALIZED_STALE` conditions, and it cannot promote knowledge.

An independent heuristic quality gate rejects empty, overly short, repeated,
candidate-data-contaminated, or lexically ungrounded responses. Passing this
heuristic **does not mean the response is factually true**. Any displayed answer
is prominently labeled `【未承認・実験的回答】` and marked
`EXPERIMENTAL_UNVERIFIED`.

## PowerShell

```powershell
git fetch origin
git switch --track origin/v0.7.11
python -m unittest -v test_experimental_quality_v0711.py test_trusted_first_router_v0710.py
```

Default Trusted-only behavior:

```powershell
python chat.py
```

Enable fallback during the current PowerShell session:

```powershell
$env:LLM_CHA_EXPERIMENTAL_FALLBACK="1"
python chat.py
Remove-Item Env:\LLM_CHA_EXPERIMENTAL_FALLBACK
```

This uses the experiment checkpoint at
`results/adapter_sweep_v077_full/r16_e30_lr1e-03/experimental-adapter.pt`
and Base checkpoint `model/model-gpu-v1.6.2-online.pt`. Both must exist
locally; if loading fails, Trusted UNKNOWN is preserved and a metadata
diagnostic is printed.

## Scope and limitations

- Only the main `UNKNOWN_KNOWLEDGE` branch was integrated; other UNKNOWN
  situations in `chat.py` are deliberately unchanged for safety.
- Wikipedia evidence and contextual followups can resolve earlier, so they
  do not automatically invoke the experimental model.
- The quality gate is heuristic. It can reject valid paraphrases and accept
  hallucinations. **No automatic truth verification** is claimed.
- No automatic approval, training, `/sleep`, or history persistence of an
  experimental answer.
- The adapter trained on a synthetic phrase is not yet ready for production
  factual responses. Holdout quality and protected QA retention must improve.
