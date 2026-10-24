import tempfile
import unittest
from pathlib import Path
from unapproved_llm_intake_v074446 import _save,_read
from backfill_unapproved_semantic_v074450 import backfill

class BackfillTests(unittest.TestCase):
    def test_backfill_preserves_and_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"knowledge.json"
            rows=[
                {"id":"one","subject":"量子ビット",
                 "natural_language":"量子ビットは量子情報の基本的な単位である。",
                 "source":"https://ja.wikipedia.org/wiki/量子ビット",
                 "truth_state":"EXTERNAL_UNVERIFIED","train_ready":False,"state":"UNAPPROVED"},
                {"id":"two","subject":"量子ビット",
                 "natural_language":"それに対して別の話題がある。",
                 "source":"https://ja.wikipedia.org/wiki/量子ビット",
                 "truth_state":"EXTERNAL_UNVERIFIED","train_ready":False,"state":"REVIEW_CONFLICT"}
            ]
            _save(p,{"version":"v0.7.44.46","candidates":rows})
            self.assertEqual(backfill(p,dry_run=True)["added"],2)
            self.assertNotIn("semantic_candidate",_read(p)["candidates"][0])
            result=backfill(p)
            self.assertEqual(result["added"],2)
            self.assertEqual(result["structured"],1)
            self.assertEqual(result["unstructured"],1)
            updated=_read(p)["candidates"]
            for old,new in zip(rows,updated):
                for key in old:
                    self.assertEqual(old[key],new[key])
            self.assertEqual(backfill(p)["added"],0)
    def test_missing_store(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(backfill(Path(d)/"missing.json")["total"],0)

if __name__=="__main__":
    unittest.main()
