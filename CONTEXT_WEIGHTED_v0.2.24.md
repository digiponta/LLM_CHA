# LLM_CHA v0.2.24 — Effective Context Supervision

v0.2.23 attempted 60 duplicate copies of six contextual records inside ordinary training JSONL. However `train_nagato_chat.load_pairs()` deduplicates exact user/assistant pairs. Thus the measured SFT had 3,006 unique records, not the desired 3,360 exposures.

v0.2.24 uses the existing supported `--expansion-data` / `--expansion-weight` channel **after pair deduplication**. The six contextual examples are placed in a separate `context.jsonl`; 3,000 ordinary replay examples in `train.jsonl`. The wrapper prints actual *expected* context, replay, and persona-anchor exposures **per epoch**, and refuses inconsistent configuration.

## PowerShell

```powershell
git fetch origin
git switch --track origin/v0.2.24
python -m unittest -v test_context_weighted_v0224.py
python prepare_context_weighted_v0224.py
python train_context_weighted_v0224.py --dry-run
python train_context_weighted_v0224.py
python evaluate_context_conditioning_v0223.py --models model/model-llm-cha-response-quality-v0221.pt model/model-llm-cha-context-conditional-v0223.pt model/model-llm-cha-context-weighted-v0224.pt --output results/context_weighted_comparison_v0224.json
```

Default exposure accounting before persona anchors: 3,000 general replay + 6 × 60 = 3,360. Nine anchors × 10 = 90; expected total 3,450 with a context fraction of ~10.43% *if all unique replay rows are distinct*. The runtime wrapper recalculates counts from actual deduplicated inputs.

**Evaluation:** matched vs shuffled context NLL on six train topics and two heldout topics; common 1,000-row independent NLL; raw Greedy generation for unseen topics; Truth/Unknown Gate regression. Holdout N=2 and six repeated synthetic contexts give weak generalization evidence. Treat as a controlled training-weight validation, not proof that the LLM understands context. Never overwrite base checkpoints.

No GPU testing is performed through GitHub.
