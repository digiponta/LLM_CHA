# LLM_CHA v0.4.28.24 — ChatGPT provisional QA × Truth Gate audit

Offline evidence audit only. Joins the registered ChatGPT-derived 64-case labels with v0.4.28.14 observed Gate comparison and original validation. Reports provisional false accepts and semantic agreement coverage. Labels remain `chatgpt` sourced, **not human ground truth**, and the results are **not measured classifier accuracy**, causality, or an independent holdout.

```powershell
git switch v0.4.0
git pull --ff-only origin v0.4.0
python -m py_compile analyze_chatgpt_qa_gate_v042824.py
python -m unittest -v test_analyze_chatgpt_qa_gate_v042824.py test_chatgpt_qa_label_exchange_v042823.py

python analyze_chatgpt_qa_gate_v042824.py `
  --validation results/semantic_probe_validation_v042812.json `
  --labels results/chatgpt_qa_labels_v042823.json `
  --comparison results/gate_relevance_comparison_v042814.json `
  --output results/chatgpt_qa_gate_audit_v042824.json
```

The script requires 64 unique aligned turns, checks ChatGPT label provenance, rejects already human-labeled comparison records rather than misrepresenting provenance, and validates available numerical Semantic Agreement. The existing comparison records have unknown root-cause attribution and may have unobserved Gate scores. Results are descriptive only. Output cannot overwrite an existing file.

Expected tests: 12 across the two modules, pending Windows execution. No Truth Gate, chat.py, Semantic Memory, /sleep, /train or model changes.
