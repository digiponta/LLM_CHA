# LLM_CHA v0.2.32.8 — Semantic Memory Expansion (controlled experiment)

Goal: test whether reviewed paraphrase expansion improves free-generation more than the same approved memory examples trained without expansion.

## Implemented
- `semantic_memory_expansion_v02328.py`: derive canonical Topic/Purposes/Relation/Action from approved memory; produce original rows (APPROVED) and *curated but unreviewed* paraphrase rows (PENDING_REVIEW).
- `train_semantic_expansion_v02328.py`: train two separate SFT checkpoints starting from the **same frozen baseline** with the same epochs/LRs/replay, differing in original-only vs expanded data. Outputs are separate and cannot overwrite the original checkpoint.
- `test_semantic_expansion_v02328.py`: verifies approvals, pair creation, exclusion of the v0.2.32.7 evaluation probes.

## Windows PowerShell

```powershell
git fetch origin
git switch v0.2.32.8
git pull origin v0.2.32.8
python -m unittest -v test_semantic_expansion_v02328.py
python semantic_memory_expansion_v02328.py export
python semantic_memory_expansion_v02328.py list
```

Inspect `data/semantic_expansion_v02328.jsonl` (especially each PENDING_REVIEW pair and its inherited answer). Approve **only meaning-preserving** examples (shown IDs consist of the memory record ID followed by `:variant:0` or `:variant:1`):

```powershell
python semantic_memory_expansion_v02328.py approve --id f8bf1478520b1dcf0969:variant:0
python semantic_memory_expansion_v02328.py approve --id f8bf1478520b1dcf0969:variant:1
python semantic_memory_expansion_v02328.py approve --id 63cf99d88bc2e0e898fe:variant:0
python semantic_memory_expansion_v02328.py approve --id 63cf99d88bc2e0e898fe:variant:1
python semantic_memory_expansion_v02328.py training

python train_semantic_expansion_v02328.py --epochs 8
```

Expected outputs:
- `model/model-llm-cha-memory-original-v02328.pt`
- `model/model-llm-cha-memory-expanded-v02328.pt`
- `results/semantic_expansion_train_v02328.json`

**Important limitation**: v0.2.32.8 only generates two controlled comparison checkpoints. To assess the actual transfer, compare those two checkpoints with *identical* never-trained evaluation prompts, greedy decoding and a reviewer-scored response-quality metric. An NLL reduction alone is not proof. Existing v0.2.32.7 probes are explicitly excluded from the curated expansion dataset; use untouched independent test cases for final judgments.

**Current design restrictions**: paraphrase templates are intentionally limited to currently supported learning and sequential-plan purposes; they are not a universal paraphrase generator. `export` will reset approvals in the separate expansion JSONL if rerun; keep reviewed data and avoid re-exporting after review. The SFT experiment does not mark Semantic Memory records INTERNALIZED, does not background schedule training, and does not bypass DSS.
