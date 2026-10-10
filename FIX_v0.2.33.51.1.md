# LLM_CHA v0.2.33.51.1 — Windows SQLite Connection Lifecycle Fix

## Incident

On Windows Python 3.13, `test_atomic_confirmation_v023351.py` raised `PermissionError: [WinError 32]` at `TemporaryDirectory.__exit__`. Three atomic test cases failed during cleanup; both existing reference-expiry tests passed. The standalone `atomic_confirmation_v023351.py` failed identically.

## Root cause

The original `with self._db() as db` relied on the built-in `sqlite3.Connection` context manager, which manages transactions but **does not close connections**. The database handle could still exist when Windows tried to delete `test.db` / `cas.sqlite`.

## Fix

`AtomicStore._db` is now an explicit `@contextmanager`: it opens the database, yields it, rolls back on errors, commits an active transaction on normal return, and **always closes** in `finally`. No CAS transition semantics or database schema changed.

## Verify

```powershell
git fetch origin
git switch v0.2.33.51.1
git pull origin v0.2.33.51.1
python -m py_compile atomic_confirmation_v023351.py
python -m unittest -v test_atomic_confirmation_v023351.py test_reference_expiration_v023350.py
python atomic_confirmation_v023351.py
```

The script still writes `results/atomic_confirmation_v023351.json` and refuses overwrite. The GitHub change is committed, but Windows runtime success has not yet been checked.

## Remaining scope

Windows file-handle fix does not establish cross-process CAS/load robustness, expiry under races, or production integration. Those remain separate experiments.
