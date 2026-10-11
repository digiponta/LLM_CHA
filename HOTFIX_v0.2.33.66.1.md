# LLM_CHA v0.2.33.66.1 — SQLite Handle Cleanup Hotfix

User's Windows Python 3.13 test run reported **20/20 errors** caused by `PermissionError: [WinError 32]` during `TemporaryDirectory.cleanup()`, attempting to unlink `candidates.db` or `candidates.sqlite3`. The errors are in cleanup; this does not by itself show that candidate parsing, review or deduplication failed.

Python's `sqlite3.Connection` context manager commits/rolls back, but **does not close the connection**. Both `CandidateStore` (v0.2.33.65) and `CorpusCandidateStore` (v0.2.33.66) used it in a way that could leave handles open.

The hotfix adds a `sqlite_session` contextmanager that enters the transaction and **always closes** the underlying SQLite connection with `finally: conn.close()`. All store operations use this wrapper. An extra regression file immediately unlinks the DB after insert/list/review, mirroring Windows strict locking.

```powershell
git fetch origin
git switch v0.2.33.66.1
git pull origin v0.2.33.66.1
python -m py_compile proposition_candidate_lifecycle_v023365.py corpus_candidate_extraction_v023366.py
python -m unittest -v test_sqlite_connection_cleanup_v0233661.py test_corpus_candidate_extraction_v023366.py test_proposition_candidate_lifecycle_v023365.py
```

Expected: **22/22 PASS** (two new tests plus the original twenty). These tests have **not** been run in the user's Windows environment yet.

No Semantic Memory promotion, Truth State adjustment, model training or `/sleep`.
