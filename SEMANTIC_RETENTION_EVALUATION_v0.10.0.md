# v0.10.0 Semantic retention evaluation

`evaluate_semantic_retention_v0100.py` compares the base Nagato checkpoint and restored online checkpoint directly, computing teacher-forced mean negative log likelihood on up to 56 existing Semantic Memory question/answer pairs. It loads model weights and tokenizer and calls the model forward pass, without running chat.py, external evidence, RAG, or training.

This is a memory-fit diagnostic, **not** independent QA accuracy or proof of internalization. The evaluation set overlaps recorded learning pairs and may be biased. Next steps require independent paraphrase holdouts, generation scoring, and unknown rejection.

Windows:

```powershell
python -m unittest -v test_evaluate_semantic_retention_v0100.py
python evaluate_semantic_retention_v0100.py --tokenizer C:/Users/inoma/git/misc/LLM_GPU/model/tokenizer-v0.7-bpe.json
```

Outputs `results/semantic_retention_v0100.json` with per-concept values. Compare `base.mean_answer_nll`, `online.mean_answer_nll`, and `online_improved`. No files are modified other than the evaluation report.
