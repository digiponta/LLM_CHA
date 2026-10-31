# LLM_CHA v0.13.58.82.89 — Complete the Holdout Review

No new training, no checkpoint promotion. The 2-epoch and 4-epoch checkpoints must remain separate.

The v0.88 Windows transcript already contains four 4-epoch holdout observations:
- daily-001 / 今日は何をしてる？ -> それは面白い。
- daily-002 / 今何してる？ -> 少し話そう。またどこが合う。
- daily-003 / 最近どう？ -> 誰が合うばよいですね。
- daily-004 / 少し話さない？ -> いいね。どんな日本語ではいいね。
The fifth `daily-005` / 今日の調子はどう？ is **not yet observed**. Existing B2 responses are from v0.84 with a different checkpoint pathname; retest the B2 v0.88 checkpoint for a strictly matched experiment.

## Windows

```powershell
cd C:\Users\inoma\git\misc\LLM_CHA
git fetch origin
git switch v0.13.58.82.89-holdout-review
python -m unittest -v test_daily_holdout_v013588289.py test_daily_sft_epochs_v013588288.py
python chat.py --model model/daily-sft-2epoch-v013588288.pt
# Ask all five holdout questions, then /exit.
python chat.py --model model/daily-sft-4epoch-v013588288.pt
# Ask all five holdout questions, then /exit.
```

Record actual output and route. Example schema for each file (one entry per question, do not copy the illustrative answer into results):
```json
{"runs":[
 {"id":"daily-001","candidate":"actual raw candidate","display":"actual displayed answer","route":"ACCEPT","human_appropriate":false}
]}
```
Save to `results/daily_observations_2epoch_v013588289.json` and `results/daily_observations_4epoch_v013588289.json`. Enter `human_appropriate: true` only where the answer actually and naturally responds to the question; otherwise `false`. Or omit ratings for later review. The script never infers semantic naturalness from punctuation or Gate status.

```powershell
python compare_daily_holdout_v013588289.py `
  --two results/daily_observations_2epoch_v013588289.json `
  --four results/daily_observations_4epoch_v013588289.json
```

Test semantic retrieval in each chat:
```
閃亜鉛鉱とは？
スファレライトとは？
```
Verify registered definition and alias behavior; keep the raw answers. This check is not automated by v0.89. **Do not promote** the 4-epoch checkpoint merely because it has lower training or teacher-forced loss. Evaluate only after 5/5 paired holdout observations and retrieval regression, and preserve the previous production model.
