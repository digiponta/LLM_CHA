import tempfile
import unittest
from pathlib import Path
from unapproved_semantic_structure_v074449 import extract_structure
from unapproved_llm_intake_v074446 import _save,_read
from backfill_unapproved_semantic_v074450 import backfill

class JapaneseRecheckTests(unittest.TestCase):
    def test_comparison(self):
        s="古典的なビットが0または1の状態のみをとるのに対し、量子ビットは重ね合わせ状態もとることができる。"
        result=extract_structure(s,"量子ビット")
        self.assertEqual(result["relation"],"can_have_superposition")
        self.assertEqual(result["comparison_subject"],"古典的なビット")
    def test_basic_unit(self):
        result=extract_structure("量子ビットは量子情報処理の基本単位である。","量子ビット")
        self.assertEqual(result["status"],"STRUCTURED")
    def test_recheck_preserves_source(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"data.json"
            sentence="古典的なビットが0または1の状態のみをとるのに対し、量子ビットは重ね合わせ状態もとることができる。"
            row={"id":"1","subject":"量子ビット","natural_language":sentence,
                 "source":"https://ja.wikipedia.org/wiki/量子ビット",
                 "truth_state":"EXTERNAL_UNVERIFIED","state":"UNAPPROVED",
                 "train_ready":False,"semantic_candidate":{"status":"UNSTRUCTURED","reason":"NO_EXPLICIT_PATTERN"}}
            _save(p,{"version":"test","candidates":[row]})
            self.assertEqual(backfill(p)["preserved"],1)
            preview=backfill(p,dry_run=True,recheck_unstructured=True)
            self.assertEqual(preview["structured"],1)
            self.assertEqual(_read(p)["candidates"][0]["semantic_candidate"]["status"],"UNSTRUCTURED")
            self.assertEqual(backfill(p,recheck_unstructured=True)["rechecked"],1)
            updated=_read(p)["candidates"][0]
            self.assertEqual(updated["semantic_candidate"]["status"],"STRUCTURED")
            for field in ("natural_language","source","truth_state","state","train_ready"):
                self.assertEqual(updated[field],row[field])
            self.assertEqual(backfill(p,recheck_unstructured=True)["added"],0)
if __name__=="__main__":unittest.main()
