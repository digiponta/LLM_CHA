"""Windows regression: after each SQLite operation, DB must be unlinkable."""
import tempfile
import unittest
from pathlib import Path
from proposition_candidate_lifecycle_v023365 import CandidateStore
from corpus_candidate_extraction_v023366 import CorpusCandidateStore

class WindowsSQLiteCloseTests(unittest.TestCase):
    def test_candidate_store_closes_every_connection(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"manual.db"
            store=CandidateStore(path)
            tokens=store.propose("ctx","GPU","GPUは並列計算に適する","test")
            self.assertEqual(len(store.list("ctx","GPU")),1)
            self.assertTrue(store.review("ctx","GPU",tokens[0],"APPROVED"))
            path.unlink()
            self.assertFalse(path.exists())
    def test_corpus_store_closes_every_connection(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            corpus=root/"corpus.txt"
            corpus.write_text("GPUは並列計算に適する。",encoding="utf8")
            path=root/"corpus.db"
            store=CorpusCandidateStore(path)
            tokens=store.propose_from_file("ctx","GPU",corpus)
            self.assertEqual(len(store.list("ctx","GPU")),1)
            self.assertTrue(store.review("ctx","GPU",tokens[0],"APPROVED"))
            path.unlink()
            self.assertFalse(path.exists())

if __name__=="__main__":
    unittest.main()
