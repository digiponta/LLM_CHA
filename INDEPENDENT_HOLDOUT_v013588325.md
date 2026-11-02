# LLM_CHA v0.13.58.83.25 — Independent Holdout Evaluation

Status: **evaluation tooling introduced; independent evaluation NOT YET RUN**.

This branch is based on `v0.13.58.83.24-rse-generalization-eval`. No RSE activation policy, `chat.py`, model checkpoint, or training files are modified.

## First run (Windows PowerShell)

```powershell
python -m unittest -v test_independent_holdout_v013588325.py
python generate_independent_holdout_draft_v013588325.py
```

The generated 50 cases are **researcher-authored development drafts**, not an independent holdout. They include 10 each of paraphrase, negation, ambiguity, multi-turn, and knowledge collision. Replace or independently author questions if they overlap model training, experiments, existing evaluations, or prompts shown to the developer. Multi-turn draft questions are single-turn prompts: reviewers must extend them into actual ordered multi-turn conversations before approval.

## Independent dataset and review

Save the separately developed and labeled dataset as `data/independent_holdout_v013588325.json` using the generated schema as a starting point. Each case requires: `id`, `category`, ordered `turns`, `expected_decision` (ADOPT/ABSTAIN/PASS_THROUGH), `review_state=APPROVED`, `reviewer`, `reviewed_at`, and human-readable `expected_answer_criteria`. Mark `protected_knowledge=true` only on factual regression cases and `unknown_expected=true` only when refusal/abstention is the correct behavior. Record human-approved independence attestation with `training_overlap=false` and `development_overlap=false`; these flags are attestations, **not automatically proven** by the scorer.

Do not modify approved holdout cases after looking at outcomes. Use a fresh independent final set when earlier cases have informed tuning.

## Paired actual runtime traces

Use the same model checkpoint, model inputs, knowledge store snapshot, and deterministic configuration (where possible) in two **actual `chat.py`** runs, with experimental RSE disabled and enabled, respectively. Record the entire conversation needed for each case, including preceding turns. Keep immutable raw transcripts and logs elsewhere, and include provenance in the run records.

Recordings JSON format:

```json
{
  "schema": "llm-cha-paired-runtime-recordings-v1",
  "dataset_digest": "SHA256 of canonical sorted-key JSON cases from the scorer",
  "same_checkpoint": true,
  "same_knowledge_state": true,
  "executed_chat_py": true,
  "cases": [
    {
      "id": "paraphrase-01",
      "off": {
        "decision": "ABSTAIN", "answer": "未学習です",
        "route": "BASELINE", "run_id": "trace-id-off", "knowledge_correct": null
      },
      "on": {
        "decision": "ADOPT", "answer": "実際の回答本文",
        "route": "RSE_APPROVED_EXPERIMENTAL", "run_id": "trace-id-on",
        "knowledge_correct": null
      }
    }
  ]
}
```

For every case, record both `off` and `on` observations. `knowledge_correct` must be independently marked true or false for protected-knowledge cases; an absent value is counted as not retained. The decision is a **human interpretation of the full observed response**, not necessarily the internal route name. Record only what actually happened. The scorer validates completeness and consistency, but it does not authenticate claims that a transcript came from `chat.py`.

## Scoring

```powershell
python evaluate_independent_holdout_v013588325.py `
  --dataset data/independent_holdout_v013588325.json `
  --recordings results/independent_runtime_recordings_v013588325.json `
  --output results/independent_holdout_v013588325.json
```

Absent review, absence of actual runtime traces, bad dataset digest, or unmatched records → **NOT_READY**, with a nonzero exit code. Present but below provisional quality gates → **FAIL**.

Provisional gates: precision >=0.90; positive coverage >=0.80; false adoption among expected non-ADOPT <=0.05; protected-knowledge retention >=0.98 and no less than baseline; unknown-case abstention accuracy >=0.90. All reported per category plus full paired dataset. Undefined metrics (no positive, unknown, or protected cases) fail the gate.

**Limits:** This tool does not run model inference, capture real live dialogue, verify independence by itself, perform statistical confidence intervals, or establish scientific factual correctness. Fifty cases are a pilot sample; present denominators, uncertainty and raw case decisions when reporting any subsequent finding.
