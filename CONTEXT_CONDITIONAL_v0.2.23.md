# LLM_CHA v0.2.23 — Context-conditioned response training

**Goal:** test whether a small 8.96M-parameter model can associate the SAME final question with different topic-specific answers given a distinct preceding dialogue.

Training: six authored topics (SF, curry, classical music, hiking, game programming, historical fiction) plus limited replay from existing v0.2.12 training data. Two authored heldout topics (photography, gardening) are excluded from replay by keywords. Validation on just two heldout samples is **high variance** and should never be treated as final generalization evidence. Synthetic repetitions may cause memorization. Only assistant tokens are supervised by the existing trainer; this does NOT add an explicit contrastive ranking loss.

Run on Windows:
```powershell
git fetch origin
git switch --track origin/v0.2.23
python -m unittest -v test_context_conditional_v0223.py
python prepare_context_conditional_v0223.py
python train_context_conditional_v0223.py --dry-run
python train_context_conditional_v0223.py
python evaluate_context_conditioning_v0223.py
```

New checkpoint: `model/model-llm-cha-context-conditional-v0223.pt`.

Evaluation reports NLL matrices: each target answer is scored under matching and mismatched topic contexts. Positive diagonal margin indicates matching context has lower NLL than every incorrect context, but does NOT establish generation quality. Follow up with v0.2.22 free-generation diagnostics and unseen dialogue probes (same question with changed context); compare the protected Semantic Memory/Truth/Unknown behavior and standard 1000-row independent NLL before adoption.

No remote CUDA tests were executed. Existing model weights are preserved.
