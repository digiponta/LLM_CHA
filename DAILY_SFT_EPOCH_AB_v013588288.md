# LLM_CHA v0.13.58.82.88 — Isolated 2-vs-4-Epoch SFT Experiment

Goal: test whether two additional epochs help the **same 60 manually authored training pairs**. This release provides an experiment protocol, path collision guard and teacher-forcing report comparator. It does **not** train or promote models in GitHub. The earlier 5 heldout daily questions remain evaluation-only. This is an exploratory test: the training pairs are not proven semantically independent of the holdout questions.

## Windows PowerShell

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.88-sft-epoch-comparison
python -m unittest -v test_daily_sft_epochs_v013588288.py test_daily_teacher_forcing_v013588287.py test_daily_sft_isolation_v013588284.py
python check_daily_sft_isolation_v013588284.py
python compare_daily_sft_epochs_v013588288.py

# Run with chat.py CLOSED. Both trials must start from the same immutable original base.
$shared = @(
 "--chat-data","data/daily_sft_train_v013588284.jsonl",
 "--base-model","model/model-gpu-v1.6.2-online.pt",
 "--tokenizer","C:\Users\inoma\git\misc\LLM_GPU\model\tokenizer-v0.7-bpe.json",
 "--learning-rate","1e-5",
 "--replay-ratio","1.0"
)
python online_train.py @shared --epochs 2 --output model/daily-sft-2epoch-v013588288.pt --state results/daily-sft-state-2epoch-v013588288.json
python online_train.py @shared --epochs 4 --output model/daily-sft-4epoch-v013588288.pt --state results/daily-sft-state-4epoch-v013588288.json

# Both diagnostics use the same seen training questions, not the holdout.
python diagnose_daily_teacher_forcing_v013588287.py --base model/model-gpu-v1.6.2-online.pt --candidate model/daily-sft-2epoch-v013588288.pt --tokenizer C:\Users\inoma\git\misc\LLM_GPU\model\tokenizer-v0.7-bpe.json --output results/teacher_force_2epoch_v013588288.json
python diagnose_daily_teacher_forcing_v013588287.py --base model/model-gpu-v1.6.2-online.pt --candidate model/daily-sft-4epoch-v013588288.pt --tokenizer C:\Users\inoma\git\misc\LLM_GPU\model\tokenizer-v0.7-bpe.json --output results/teacher_force_4epoch_v013588288.json
python compare_daily_sft_epochs_v013588288.py --report-2 results/teacher_force_2epoch_v013588288.json --report-4 results/teacher_force_4epoch_v013588288.json
```

## Independent holdout and retention

For each candidate run `python chat.py --model model/daily-sft-2epoch-v013588288.pt` and `python chat.py --model model/daily-sft-4epoch-v013588288.pt`. Ask all five unchanged v0.83 holdout questions and record the raw candidate, gate and displayed reply in separate JSON observation files following `daily_conversation_eval_v013588283.py`. Use that tool for surface and fallback summaries, but **human evaluation of appropriateness remains essential**. Also check `閃亜鉛鉱とは？` and `スファレライトとは？` for memory-retrieval regressions.

## Interpreting the experiment

- The training program uses early stopping; an `--epochs 4` setting is a **limit**, not a guarantee that four epochs execute. Record actual best epoch, train loss and validation loss from each log.
- Both models must start from the **original** base, not from the 2-epoch candidate. Each state path is distinct; production checkpoint is not overwritten.
- The pre-existing trainer may modify candidates if they already exist. Ensure these are new experiment filenames or back them up first. `compare_daily_sft_epochs_v013588288.py` checks path equality, not full immutability and not semantic holdout independence.
- A reduction in teacher-forced loss on training questions alone is not evidence of conversational improvement. The holdout response quality and non-regression decide whether the extra epochs helped.
