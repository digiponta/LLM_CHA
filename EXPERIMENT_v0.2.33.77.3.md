# v0.2.33.77.3 — Prompt / Tokenizer Type Integrity

The user captured a genuine subprocess stack trace: `chat.py:1288` -> `BPETokenizer.encode` -> Hugging Face `backend.encode` raising `TypeError: TextInputSequence must be str`.

Inspection of `build_prompt` shows it returns `str`; the conversational path also builds a `str`. The offending runtime value **has not been directly observed**, so it would be incorrect to assert the bug is fixed. This version instead:
- checks `prompt` type at the entry to `generate_reply`
- checks `text` type at the entry to `BPETokenizer.encode`
- wraps backend TypeError with a type/length diagnosis, preserving the original traceback
- adds 5 offline regression tests using fake backends

It deliberately **does not force conversion via `str(prompt)`**, mutate model weights or change response policies.

## PowerShell

```powershell
git fetch origin
git switch v0.2.33.77.3
git pull origin v0.2.33.77.3
python -m py_compile chat.py tokenizer_bpe.py
python -m unittest -v test_tokenizer_type_integrity_v0233773.py test_runtime_startup_preflight_v0233772.py
python chat_runtime_benchmark_v023377.py --run --timeout 240
```

Inspect `diagnostic` and `stderr_tail` in `results/chat_runtime_v023377.json` if the subprocess fails again. If it reads `BPETokenizer backend rejected a str input`, investigate the installed `tokenizers` package and an isolated `BPETokenizer.load(...).encode("こんにちは")` smoke test instead of changing the prompt builder blindly.

This is diagnostic hardening until the root cause is established.
