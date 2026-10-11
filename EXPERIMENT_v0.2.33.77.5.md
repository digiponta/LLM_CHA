# LLM_CHA v0.2.33.77.5 — Windows UTF-8 Subprocess Fix

The uploaded runtime report showed `こんにちは` becoming `こ�sぃHぁBぃb` inside the isolated child process, with broken Unicode in output and a subsequent `TextInputSequence must be str` failure. The parent `subprocess.run` decoded/encoded UTF-8, but child Python's console/pipe encoding was not explicitly set. This change forces `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` on the *child subprocess*, leaving the parent runtime unchanged.

Three regression tests check UTF-8 environment settings and a real Python subprocess Japanese round-trip.

PowerShell:

```powershell
git fetch origin
git switch v0.2.33.77.5
git pull origin v0.2.33.77.5
python -m py_compile chat_runtime_benchmark_v023377.py
python -m unittest -v test_windows_utf8_subprocess_v0233775.py test_chat_runtime_benchmark_v023377.py
python chat_runtime_benchmark_v023377.py --run --timeout 240
```

Inspect `results/chat_runtime_v023377.json`. Expect no mojibake; the four chat scenarios remain subject to actual GPU execution and local truth states, and are not yet claimed PASS. The earlier scalar-to-batch Tokenizer workaround remains present but UTF-8 should prevent the offending corrupted inputs. No model or Semantic Memory data is intentionally modified.
