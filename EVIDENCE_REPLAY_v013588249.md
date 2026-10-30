# LLM_CHA v0.13.58.82.49 — GUI Evidence Replay Evaluation

This branch adds `compare_evidence_replay_v013588249.py`. It compares the original checkpoint and the three-step negative-only candidate using the **exact CLI evidence-candidate prompt construction** (`evidence_aware_route_v013588236.generation_prompt`), the GUI excerpt truncation via `encode_request/decode_request` (450 chars), and the CLI candidate decoding policy (greedy, seed=0, max 120 tokens). The same evidence object is passed through `final_answer` to record each Evidence Gate decision.

For every model, the report includes the actual generated candidate, gate status, first-generation-token Top-1/Top-2 probability and margin, and the negative teacher signal's conditional NLL **under the evidence-conditioned prompt**. The evidence response is saved separately so future reruns can use `--evidence-json`.

## Windows PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.49-evidence-replay
python -m unittest -v test_evidence_replay_v013588249.py test_negative_generation_comparison_v013588248.py
python compare_evidence_replay_v013588249.py `
  --base model/model-gpu-v1.6.2-online.pt `
  --candidate results/negative_only_v013588247_steps3.candidate.pt `
  --tokenizer C:\Users\inoma\git\misc\LLM_GPU\model\tokenizer-v0.7-bpe.json `
  --negative-data data/negative_teacher_signals_v013588244.jsonl `
  --output results/evidence_replay_v013588249.json
Get-Content results/evidence_replay_v013588249.json -Encoding UTF8
```

To repeat the *same* evidence snapshot later, pass `--evidence-json results/evidence_snapshot_v013588249.json`; live Wikipedia retrieval can otherwise change between runs. If wanting a specific original GUI passage, supply its captured evidence JSON instead of the refreshed Wikipedia result.

The evaluator bypasses the GUI's previously-rejected cache intentionally to test raw model generation; it does not change `chat.py`, `chat_gui.py`, the production model, or the negative signal queue. A changed sentence or gate does not establish universal model quality. The first-token margin is a diagnostic, not a full-sequence Top-K rank measure. No model hyperparameter search or automatic promotion occurs.
