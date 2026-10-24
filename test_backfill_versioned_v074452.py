import tempfile
import unittest
from pathlib import Path
from backfill_unapproved_semantic_v074450 import backfill
from unapproved_llm_intake_v074446 import _read,_save
from unapproved_semantic_structure_v074449 import EXTRACTOR_VERSION

class VersionedBackfillTests(unittest.TestCase):
    def test_unstructured_rechecked_only_once_per_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"store.json"
            row={"id":"one","subject":"量子ビット","natural_language":"それに対して他の状況がある。",
                 "state":"UNAPPROVED","truth_state":"EXTERNAL_UNVERIFIED","train_ready":False,
                 "source":"https://ja.wikipedia.org/wiki/量子ビット",
                 "semantic_candidate":{"status":"UNSTRUCTURED","reason":"NO_EXPLICIT_PATTERN"}}
            _save(path,{"version":"v0.7.44.46","candidates":[row]})
            preview=backfill(path,dry_run=True,recheck_unstructured=True)
            self.assertEqual(preview["changed"],1)
            self.assertNotIn("extractor_version",_read(path)["candidates"][0]["semantic_candidate"])
            first=backfill(path,recheck_unstructured=True)
            self.assertEqual(first["rechecked"],1)
            self.assertEqual(first["changed"],1)
            updated=_read(path)["candidates"][0]
            self.assertEqual(updated["semantic_candidate"]["extractor_version"],EXTRACTOR_VERSION)
            for key in ("natural_language","source","state","train_ready","truth_state"):
                self.assertEqual(updated[key],row[key])
            second=backfill(path,recheck_unstructured=True)
            self.assertEqual(second["added"],0)
            self.assertEqual(second["rechecked"],0)
            self.assertEqual(second["changed"],0)
    def test_force_does_not_write_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"store.json"
            _save(path,{"version":"test","candidates":[{
                "id":"one","subject":"量子ビット",
                "natural_language":"量子ビットは量子情報の基本単位である。"}]})
            backfill(path)
            self.assertEqual(backfill(path,force=True)["changed"],0)

if __name__=="__main__":
    unittest.main()
