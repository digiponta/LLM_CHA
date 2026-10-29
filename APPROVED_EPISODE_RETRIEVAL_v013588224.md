# v0.13.58.82.24 — Approved Episodic Semantic Retrieval

This increment reads the approval-gated local JSON store created in v0.13.58.82.23 on every historical query; approved records are available in a freshly started GUI process.

Recognized historical prompts: `以前、何を飲んだ？`, `以前、何を食べた？`, `以前、好きな商品は？`, `以前、どの商品に満足した？`. A follow-up `その時は満足した？` refers to one unambiguously selected approved episode; with no unique selected episode it requests clarification instead of guessing. Regular session-only queries still use the preexisting EpisodeContext.

Safety constraints: only records with `APPROVED`, `USER_SELF_REPORTED`, `ACTIVE`, and a valid episode ID/subject are eligible. Never turn a preference into consumption; never claim satisfaction without recorded normalized positive satisfaction. Revoked records disappear from subsequent queries. No automated Semantic Memory promotion, /sleep training, SKI exchange or model-weights updates.

## Windows testing
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.24-approved-episode-retrieval
python -m unittest -v test_approved_episode_retrieval_v013588224.py test_episodic_memory_gate_v013588223.py test_episodic_retrieval_v013588222.py
python chat_gui.py
```
Using previously approved black-ear drink episode, restart the GUI and input `以前、何を飲んだ？` followed by `その時は満足した？`. Confirm no new approval is requested and no unapproved episodes are imported. Verify `/episode revoke <UUID>` and retry the historical query.

Limitations: deliberately narrow Japanese question patterns and one-episode follow-up; it does not yet merge current-session and historical results or provide a full multi-turn reference solver. The local approved JSON is private self-reported conversation data and should not be committed to Git.
