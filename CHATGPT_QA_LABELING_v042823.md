# LLM_CHA v0.4.28.23 — ChatGPT-driven QA Relevance Labeling

This workflow replaces manual first-pass labeling with ChatGPT review while preserving AI provenance. The ChatGPT judgments are *provisional model-generated annotations*, NOT human ground truth. This version does not call any API: export a packet and upload it to ChatGPT; ask ChatGPT to return a JSON file following the response contract; then import that file locally. The original CSV remains untouched.

## 1. Export all 64 cases in Windows PowerShell

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile chatgpt_qa_label_exchange_v042823.py
python -m unittest -v test_chatgpt_qa_label_exchange_v042823.py
python chatgpt_qa_label_exchange_v042823.py `
  --validation results/semantic_probe_validation_v042812.json `
  --export-packet yes `
  --output results/chatgpt_qa_packet_v042823.json
```

Upload `results/chatgpt_qa_packet_v042823.json` into ChatGPT (this conversation). Request: “64件のquestionとfinal_answerを1件ずつ評価してください。回答が質問に適切に対応していれば relevant=true、不適切ならfalse、判定できないときはnull。各件に短い日本語の理由を付けてください。ID、turnを変えず、すべての件を含むJSONファイルを作成してください。推測した回答を生成・置換しないでください。”

## 2. Required ChatGPT output structure

```json
{
  "schema":"llm_cha_chatgpt_qa_v1",
  "label_source":"chatgpt",
  "decisions":[
    {"id":"A04","turn":1,"relevant":false,"reason":"質問への応答になっていない"}
  ]
}
```

The example above is a fragment; the submitted JSON **must contain all 64 cases exactly once**. The tool accepts true/false/null and validates the exact IDs and turns against the original packet generated from the validation report. The output records all decisions as ChatGPT-source and explicitly sets human_ground_truth=false.

## 3. Import ChatGPT output

Save the generated ChatGPT JSON to `results/chatgpt_qa_labels_v042823.json`, then run:

```powershell
python chatgpt_qa_label_exchange_v042823.py `
  --validation results/semantic_probe_validation_v042812.json `
  --import-labels results/chatgpt_qa_labels_v042823.json `
  --output results/chatgpt_qa_reviewed_v042823.json
```

No output is overwritten. The existing manual-label CSV `results/qa_review_worksheet_v042820_fixed.csv` remains unchanged and no human labels are forged. GPT results must be independently audited on a representative sample before any calibration, quality or accuracy claim. No changes to Truth Gate, chat.py, /sleep, /train, Semantic Memory, or model weights.

Important: the command flag `--export-packet yes` is an export selector, not a path; only `--output` sets the target.
