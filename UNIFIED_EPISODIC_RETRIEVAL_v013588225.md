# v0.13.58.82.25 Unified Episodic Retrieval

Queries such as "何を飲んだ？", "好きな商品は？", "どの商品に満足した？" now search both in-memory sessions and **approved** local records with provenance labels. Matching snapshot records are deduplicated by topic/subject/action/observations, not merely product name; a session preference does not imply consumption. Follow-up "その時は満足した？" is only answered after a unique episode match. Deleted approved records are checked again before follow-up.

Only explicitly approved and active USER_SELF_REPORTED records from the persistent JSON file are eligible. Staged/pending records are excluded, and Wikipedia/clipboard Evidence is not promoted. This does not modify model weights or train LLM/SEM.

Windows:
```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.25-unified-episodic-retrieval
python -m unittest -v test_unified_episode_retrieval_v013588225.py test_approved_episode_retrieval_v013588224.py test_episodic_memory_gate_v013588223.py
python chat_gui.py
```

Try with a previously approved black-ear drink episode and new session preference for café americano. Ask "何を飲んだ？", "好きな商品は？", "どの商品に満足した？", then "その時は満足した？".

Limits: exact-phrase Japanese question recognition, not general semantic search. Deduplication depends on identical canonical observations, so amended or paraphrased snapshots may remain distinct. Outputs explicitly distinguish provenance and approval state.
