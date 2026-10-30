# LLM_CHA v0.13.58.82.62 — Alias-Aware Relation Binding

Adds `evidence_alias_binding_v013588262.py`, an offline-only binder extending v0.59 with:
- スファレライト → 閃亜鉛鉱, explicit 硫化亜鉛 → ZnS on a source-grounded sentence
- 水の化学組成 → H2O only when explicitly present in a matching-source sentence
- 中央処理装置 → CPU definition sentence, with a conservative syntactic pattern
- subject mismatch rejection before all relation logic (prevents unrelated source acceptance)

The selected full sentence must pass the original exact-source Evidence Gate; normalized formula values are separate metadata, not claims that the text literally says ZnS. Public Wikipedia source excerpts are still EXTERNAL_UNVERIFIED, truncated at 900 chars, and PENDING_HUMAN_REVIEW.

`evaluate_alias_binding_v013588262.py` compares the new binder against (a) 8 captured Wikipedia records for diagnostic status only, and (b) the original 12 synthetic labeled fixtures for quantitative preservation. Do not interpret real-source extraction count as answer accuracy. Independent holdout review remains incomplete. No changes to production GUI, checkpoint or learning.

## Windows PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.62-alias-aware-binding
python -m unittest -v test_evidence_alias_binding_v013588262.py test_evidence_cause_binding_v013588259.py test_evidence_alias_review_v013588261.py
python evaluate_alias_binding_v013588262.py `
  --real-data data/wiki_evidence_review_v013588260.json `
  --synthetic-data data/independent_binding_eval_v013588258.json `
  --output results/alias_binding_v013588262.json
Get-Content results/alias_binding_v013588262.json -Encoding UTF8
```

Review each `real.cases` entry; in particular, expect explicit values in the Sphalerite and Water records and a source-exact CPU definition if the conservative sentence matcher permits it. The 12 synthetic fixtures should retain zero false acceptance. Do not mark reviews approved without actual human verification and source independence evidence.
