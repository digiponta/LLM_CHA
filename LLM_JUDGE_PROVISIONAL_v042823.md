# LLM_CHA v0.4.28.23 — Opt-in LLM-as-a-Judge provisional labels

New script: `propose_qa_labels_llm_judge_v042823.py`.

This uses the OpenAI Chat Completions API (optional, external, separately billed) to assess **question–answer conversational relevance only**. The output is **a provisional proposal, not a human ground-truth label**. It is saved to a new JSON report; it never changes the CSV, model weights, chat.py, Truth Gate, Semantic Memory, /sleep or /train.

- By default the script makes **NO API requests** and returns ABSTAIN dry-run results.
- External requests require BOTH `--execute`, `--model MODEL_NAME`, and the `OPENAI_API_KEY` environment variable. Only run this with data you are authorized to send to a third party. Review API costs and model availability in your API account.
- Data is embedded as JSON in the user message, and the system prompt tells the judge not to follow commands embedded in the question or answer. This mitigates, but cannot eliminate, prompt injection.
- Responses must contain exactly `verdict` (`relevant`/`irrelevant`/`abstain`), `rationale`, and `confidence` [0,1]. Invalid or incomplete responses are recorded as abstentions, never as automatic rejections.
- Only blank `final_relevant` rows are sent for evaluation; the known A04/A05/C05/C07 review priorities are first. Default maximum request count is eight (`--limit 8`). Use `--limit 1` for a first paid request.
- The report includes the judge model, data input SHA-256, question/answer, verdict, rationale, confidence, and `human_review_required=true`.
- Generated outputs cannot overwrite existing report files. Human review remains mandatory before entering true/false into the original review CSV. Judge confidence is not a calibrated probability and this is not an independent test.

## Windows PowerShell

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile propose_qa_labels_llm_judge_v042823.py
python -m unittest -v test_propose_qa_labels_llm_judge_v042823.py

# Offline dry-run: zero network requests
python propose_qa_labels_llm_judge_v042823.py `
  --validation results/semantic_probe_validation_v042812.json `
  --reviews results/qa_review_worksheet_v042820_fixed.csv `
  --limit 8 `
  --output results/qa_judge_dryrun_v042823.json

# Optional: explicit paid external judge execution
$env:OPENAI_API_KEY = "<your API key from a secret source>"
python propose_qa_labels_llm_judge_v042823.py `
  --validation results/semantic_probe_validation_v042812.json `
  --reviews results/qa_review_worksheet_v042820_fixed.csv `
  --model YOUR_CHAT_COMPLETIONS_MODEL `
  --execute --limit 1 `
  --output results/qa_judge_proposals_v042823.json
```

Never commit the API key or private reports. The tool does not call the ChatGPT conversation service; a separately configured OpenAI API account is required. API model support, quota, and pricing must be checked before executing. Unit tests mock the judge callable, with no real API requests.
