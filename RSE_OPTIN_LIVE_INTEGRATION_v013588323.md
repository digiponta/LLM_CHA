# LLM_CHA v0.13.58.83.23 — Opt-in Live Theme RSE (Experimental)

This version modifies `chat.py` only on this feature branch. Default running `python chat.py` does not activate Theme RSE. Enable with `--rse-live-experiment` to insert an RSE decision **after existing deterministic/grounded and knowledge-dispatch routes** and **before generic model generation**.

Supported narrow intents: INVITE_CONVERSATION, CURRENT_ACTIVITY. Other requests remain on existing runtime. For covered intents: approved candidate meeting Theme+Intent+Time+Answer Relation -> RSE_APPROVED_EXPERIMENTAL; otherwise -> 「未学習です」 (RSE_UNLEARNED_EXPERIMENTAL / RSE_REVIEW_REQUIRED_EXPERIMENTAL). A malformed store fails closed. Memory atomic exact and other earlier retrieval paths are not touched.

Current user-local `conversation_invite_v1` has already been REVOKED. To make a new reviewed candidate:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.83.23-optin-live-rse
python -m unittest -v test_rse_live_route_v013588323.py test_rse_candidate_lifecycle_v013588322.py
python rse_candidate_lifecycle_v013588322.py register --id conversation_invite_v2 --question "少しお話ししませんか？" --answer "もちろん。何について話しましょう？" --source "reviewed-local-example"
python rse_candidate_lifecycle_v013588322.py approve --id conversation_invite_v2 --reviewer local-human
python chat.py --rse-live-experiment
```
Test:
```text
You> 閃亜鉛鉱とは
AI> 閃亜鉛鉱は、亜鉛の硫化鉱物である。
[route=MEMORY_ATOMIC_EXACT]
You> 少しお話ししませんか？
AI> もちろん。何について話しましょう？
[route=RSE_APPROVED_EXPERIMENTAL, candidate=conversation_invite_v2]
You> 今何してる？
AI> 未学習です
[route=RSE_UNLEARNED_EXPERIMENTAL, candidate=-]
```
Existing `chat.py` normal run should still behave as before (including its prior weak generic responses). The new bridge intentionally handles only two intents, not all conversation. Other earlier runtime routes may take precedence if their data changes. This is an opt-in experiment, not a validated production improvement. Model checkpoint and Semantic Memory stores remain untouched; `register`/`approve` explicitly modify only the separate lifecycle store.

Future: compare actual live logs with control run and add independence-tested holdout coverage, before expanding coverage or enabling by default.
