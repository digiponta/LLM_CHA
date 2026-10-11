# v0.2.33.77.4 — Tokenizer Backend Compatibility Fix

Observed on Windows Python 3.13: scalar Hugging Face Tokenizers `backend.encode(text, add_special_tokens=False)` raises `TextInputSequence must be str` although `text` is independently confirmed as Python `str` (45 characters).

This change adds a **narrow compatibility fallback**: on that exact backend error, call `backend.encode_batch([text], add_special_tokens=False)[0]`. Both paths use the same tokenizer backend and special-token behavior. All other exceptions propagate; if the batch API also fails, a combined diagnostic is raised. This is a targeted workaround, not proof of the underlying cause, and is not guaranteed to work on the user's installation until tested.

## Run

```powershell
git fetch origin
git switch v0.2.33.77.4
git pull origin v0.2.33.77.4
python -m py_compile tokenizer_bpe.py chat.py
python -m unittest -v test_tokenizer_backend_fallback_v0233774.py test_runtime_startup_preflight_v0233772.py
python chat_runtime_benchmark_v023377.py --run --timeout 240
```

If the benchmark still fails, paste the complete `diagnostic` and `stderr_tail`. This branch does not change model weights, stored semantic facts or Truth State.
