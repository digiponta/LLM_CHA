# v0.2.32.7 — Semantic Memory-to-LLM Transfer Validation

**Research question:** Did supervised learning from reviewed Semantic Memory improve the frozen-base LLM's *actual generated answers*, including paraphrases not seen in SFT?

## Design

- Baseline: `model/model-llm-cha-response-quality-v0221.pt`.
- Candidate: checkpoint that the v0.2.32.6 learning worker put into `VALIDATING`.
- Run both with same tokenizer, greedy temperature 0, token budget, and prompt.
- Probe families: approved teaching pairs; 4 new LLM-related paraphrases; 3 other-purpose controls; 6 legacy conversation prompts.
- Store output, generation tokens and latency in `results/semantic_transfer_eval_v02327.json`.
- Manual review fields initialized as **null**, *not* fabricated scores.
- Set `promotion_eligible=false` until independently evaluated. No automatic INTERNALIZED state transition or switching.

### Windows execution

```powershell
git fetch origin
git switch v0.2.32.7
git pull origin v0.2.32.7

python -m unittest -v test_semantic_transfer_v02327.py

python evaluate_semantic_transfer_v02327.py `
  --memory data/dss_semantic_memory_v02325.jsonl `
  --base model/model-llm-cha-response-quality-v0221.pt `
  --tokenizer model/tokenizer-v0.7-bpe.json
```

You should see entries labeled `teacher`, `unseen`, `control` and `legacy`. Compare outputs carefully. If outputs on unseen prompts remain unhelpful, the hypothesis that meaningful generation capability was internalized is **not supported** even when train NLL fell.

**Limitations:** The probes are authored specifically for this experiment and contain just four unseen LLM paraphrases. Four of the legacy cases overlap the legacy replay examples used during learning; evaluate the two unseen legacy prompts separately and collect more independently authored controls. The prompts contain labels of purpose and topic, so they test *response generation conditional on external structure*, not yet DSS-free natural-input capability. No statistical significance can be inferred from this tiny pilot. A higher-quality generalization test should be preregistered, authored independently and use several different training seeds and broad topic/purpose distributions.

**Next:** Withhold promotion, expand independently authored assessment, and test both (1) labelled Short DSS prompts and (2) native raw chat prompts without any DSS metadata. Only the latter, together with a robust capability router, can substantiate the stronger claim that DSS is no longer needed at runtime. Also avoid using the same evaluation probes for further training if they will be used as final holdout.
