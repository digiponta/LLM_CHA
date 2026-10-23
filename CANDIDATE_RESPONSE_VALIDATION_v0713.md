# LLM_CHA v0.7.13 — Candidate-Aware Answer Consistency Gate

The v0.7.12 real runtime integration rejected the **correct** experimental
test answer `候補の実験回答です。` because a broad lexical blacklist
mistook the legitimate registered answer for accidental training leakage.

v0.7.13 makes the GATE_REVIEW candidate fallback compare experimental
generation with the **exact answer belonging to the matching PENDING record**.

- Exact question + PENDING record + exact expected answer: display with
  `EXPERIMENTAL_UNVERIFIED`, `auto_promote=False`.
- Wrong answer, even if fluent: reject to Trusted UNKNOWN.
- Malformed, empty, or unrelated response: reject.
- Approved/non-pending question or non-matching question: no candidate fallback.
- No normal Trusted-path behavior or model weights are changed.

This validates consistency with experimental training data **only**. It does
NOT establish factual correctness, and could reproduce bad unapproved data.

## Windows

```powershell
git fetch origin
git switch --track origin/v0.7.13
python -m unittest -v test_candidate_response_validation_v0713.py test_candidate_aware_fallback_v0712.py test_experimental_quality_v0711.py
$env:LLM_CHA_EXPERIMENTAL_FALLBACK="1"
python chat.py
Remove-Item Env:\LLM_CHA_EXPERIMENTAL_FALLBACK
```

Test the PENDING question `v072実験の合言葉は何ですか`.
The integrated `chat.py` still triggers on the narrow low-agreement
GATE_REVIEW path. If the Experimental Adapter reproduces its exact registered
answer, it will be displayed as **unapproved**; otherwise UNKNOWN remains.

Future work: independent factual verification and approved response retention
benchmarks; flexible Candidate matching must not weaken trust boundaries.
