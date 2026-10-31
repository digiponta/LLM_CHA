# v0.13.58.82.85 — Minimal SFT Failure Diagnosis

This release adds a **read-only checkpoint-fingerprint diagnostic**, not another training cycle.

## Confirmed from existing code and user logs

- The 60 new pairs were trained successfully for 2 epochs: validation loss 3.893 -> 2.839.
- The five unseen daily-chat probes did not yield natural, appropriate answers after training.
- Repeating the identical command with the **original base checkpoint** retrained all 60 pairs, despite the learning state being populated.
- The trainer selects pending rows if a fingerprint is absent from **either** the base checkpoint metadata or training state. That is, `not_in_checkpoint OR not_in_state`. An unchanged old base still lacks all 60 fingerprints, so this repeated training is consistent with the implemented policy.
- The candidate checkpoint contains the 60 additional fingerprints. Using it as the base with the same state should yield NO_NEW_PAIRS (exit code 3); do not run training merely to check this—use the diagnostic below.
- The initial model's checkpoint loss 0.873 and the SFT validation loss 2.839 are measured on different data; **do not interpret them as a common benchmark**.

## Windows checks

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.85-sft-diagnostics
python -m unittest -v test_daily_sft_binding_v013588285.py test_daily_sft_isolation_v013588284.py

python diagnose_daily_sft_binding_v013588285.py
```

Expected from the observed training run (verify the report rather than assuming): `present_in_state=60`, `present_in_original_base=0`, `present_in_candidate=60`, `retrain_if_original_base=60`, `retrain_if_candidate_base=0`.

## Generate versus memorize: small follow-up

Test three **training** prompts with model B using `python chat.py --model model/daily-sft-candidate-v013588284.pt`: `おはよう`, `雑談しよう`, `相談がある`. Record *raw candidate*, gate, and final output. Compare the same prompts with model A. The five holdout prompts must **remain excluded from training**. If even these seen examples fail, inspect tokenizer, first response-token probability, teacher-forced answer loss, and decoding before increasing data. If seen prompts work but holdout prompts fail, investigate generalization and dataset diversity. Keep the existing knowledge-retrieval probes as regression checks.

No checkpoint is promoted or modified. The diagnostics distinguish *why repeated training occurred* from *whether the language model learned usable conversation*. They do not claim either cause has already been fully explained.
