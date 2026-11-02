# LLM_CHA v0.13.58.83.25 — Independent Holdout Preparation (Pre-release)

Release type: **experimental / pre-release**. This release does **not** assert completion of independent holdout validation.

## Included

- Independent holdout pilot scoring tool and developer-only 50-case draft generation.
- Explicit review status: 50 cases pending; developer review pack adds ten multi-turn contexts.
- Audits of exact normalized text matches against user-provided corpora; JSON and JSONL nested utterance extraction.
- Missing source files, malformed JSONL, and comparison limitations reported.
- `chat.py`: startup diagnostic shows RSE opt-in mode. RSE remains **OFF by default**; approved candidate lifecycle remains authoritative.
- `chat_gui.py`: opt-in **RSE実験** checkbox launches `chat.py --rse-live-experiment`; changing mode restarts chat runtime, clearing transient context.
- Existing GUI search, clipboard, status and restart controls remain in the source.

## Verification evidence

- Windows PowerShell: **21/21** holdout/development audit tests PASS, as reported by project operator **before** the latest CLI/GUI changes.
- Latest CLI/GUI changes include `test_chat_rse_gui_wiring_v013588325.py`, **not yet reported as executed on Windows**.
- No successful GUI launch, actual model inference, or RSE ON/OFF dialogue comparison has been supplied after these changes.
- 50 development cases remain **PENDING** and are not a clean independent test set.
- Comparing seven source files reported no exact matches; this **does not establish semantic or training-data independence**.

## Test and run

```powershell
git fetch origin
git switch v0.13.58.83.25-independent-holdout
git pull --ff-only
python -m unittest -v test_chat_rse_gui_wiring_v013588325.py
python -m unittest -v test_independent_holdout_v013588325.py test_holdout_draft_audit_v013588325.py test_holdout_audit_missing_path_v013588325.py test_holdout_jsonl_audit_v013588325.py test_holdout_review_pack_v013588325.py
python chat_gui.py
# CLI, opt-in only:
python chat.py --rse-live-experiment
```

## Remaining release gates

1. Run the new GUI wiring tests and GUI launch on Windows.
2. Review 50 development cases independently; do not mark AI recommendations as human approval.
3. Prepare a genuinely independent human-reviewed holdout.
4. Run paired `chat.py` executions under identical checkpoints and knowledge snapshots, RSE OFF vs ON.
5. Report precision, coverage, false adoption, known-fact retention and unknown abstention.

Avoid promoting this pre-release as stable or merging into `main` until these gates are met.
