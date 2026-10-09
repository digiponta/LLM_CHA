# LLM_CHA v0.2.32.5 — DSS → Semantic Memory → LLM staged internalization

## Architecture

```text
User → DSS (purpose / relation / dialogue control)
            ↓
   Semantic Memory [MEMORIZED, PENDING_REVIEW]
            ↓ human review of a concrete teacher answer
   Semantic Memory [APPROVED] → Training Queue
            ↓ proposed asynchronous candidate checkpoint training
          TRAINING
            ↓ candidate checkpoint artifact
          VALIDATING
            ↓ independent free-generation, unseen, retention, purpose-fidelity evidence
        INTERNALIZED
            ↓
     eligible for LLM Direct routing
   (otherwise DSS fallback; rollback on failure)
```

**Current implementation boundaries:** this version implements memory capture, review, queue selection, lifecycle validation, and an **advisory** routing decision. It does *not* yet run training in the background, launch workers, hot-swap checkpoints, or route actual inference to a promoted model. `LLM_DIRECT_ELIGIBLE` is metadata; it is not itself proof of actual runtime behavior. Promotion evidence keys are explicit booleans supplied by an external evaluator and must not be automatically set from teacher loss alone.

### Data policy

The DSS is a **structure/action teacher**, not a guaranteed truth source. Store its short controller response as `dss_response`; require a separately reviewed `approved_answer` before queuing any training example. Store provenance and preserve promotion evidence on repeated inputs. Confirmation/clarification actions are not eligible for automatic SFT examples. Avoid persisting personal/private dialogue content without user consent in future production use.

### Files

- `staged_semantic_internalization_v02325.py`: JSONL Semantic Memory, review queue, lifecycle and prototype CLI.
- `test_staged_semantic_internalization_v02325.py`: regression of review, dedupe, lifecycle, promotion and fallback.

### Windows

```powershell
git fetch origin
git switch v0.2.32.5
git pull origin v0.2.32.5
python -m unittest -v test_staged_semantic_internalization_v02325.py
python staged_semantic_internalization_v02325.py
```

The interactive demo accepts a normal utterance, `/state`, `/queue`, `/reset`, `/quit`. Unreviewed records are not queued, so `/queue` will be empty until reviewed through the Python API `approve(path, id, answer)`. That is intentional.

### Future implementation plan

1. **v0.2.32.6**: implement a supervised queue-to-SFT worker, reuse existing response-only SFT code, save candidate checkpoint separately. Provide worker job status and limits; do not presume a service is running when the CLI exits.
2. **v0.2.32.7**: independent free-generation validation, held-out paraphrases and prior-capability preservation; reject and roll back if any gate fails.
3. **v0.2.32.8**: implement actual inference routing, safe checkpoint swapping and DSS fallback based on validated capability scope.
4. **v0.2.32.9**: continuous capture, revalidation and rollback lifecycle, and future automation scheduling.

A passing SFT loss or a successful backend job is **not** sufficient for INTERNALIZED promotion.
