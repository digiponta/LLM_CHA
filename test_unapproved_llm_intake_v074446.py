import tempfile
import unittest
from pathlib import Path
from unapproved_llm_intake_v074446 import ingest_wikipedia,inspect_candidates

WIKI={"status":"FOUND","title":"量子ビット","url":"https://ja.wikipedia.org/wiki/量子ビット",
      "extract":"量子ビットは量子情報科学および量子コンピュータにおいて情報を表現するための基本単位である。古典的なビットと異なり重ね合わせ状態をとることができる。"}
class UnapprovedIntakeTests(unittest.TestCase):
    def test_intake_dedup_and_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"intake.json"
            first=ingest_wikipedia(WIKI,path)
            self.assertEqual(first["status"],"STORED")
            self.assertGreaterEqual(first["added"],1)
            second=ingest_wikipedia(WIKI,path)
            self.assertEqual(second["added"],0)
            self.assertEqual(second["duplicates"],first["added"])
            result=inspect_candidates(path)
            self.assertFalse(result["model_weights_updated"])
            for item in result["candidates"]:
                self.assertEqual(item["truth_state"],"EXTERNAL_UNVERIFIED")
                self.assertFalse(item["train_ready"])
                self.assertFalse(item["weight_training"])
                self.assertFalse(item["approved_memory_export"])
    def test_invalid_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"intake.json"
            result=ingest_wikipedia(dict(WIKI,url="https://example.com/x"),p)
            self.assertEqual(result["status"],"INVALID_SOURCE")
    def test_no_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(ingest_wikipedia(None,Path(tmp)/"i.json")["status"],"NO_SOURCE")
if __name__=="__main__":unittest.main()
