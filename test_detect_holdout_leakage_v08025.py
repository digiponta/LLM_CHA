import json
import tempfile
import unittest
from pathlib import Path
from detect_holdout_leakage_v08025 import inspect


class HoldoutLeakageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.source, self.store = root/"holdout.json", root/"store.json"
        self.store.write_text(json.dumps({"candidates": [
            {"id": "trained-1", "subject": "量子センサー",
             "natural_language": "量子センサーは量子状態を利用して物理量を測定する。"}
        ]}, ensure_ascii=False), encoding="utf-8")

    def make(self, question, answer, encoding="utf-8"):
        self.source.write_text(json.dumps({"records": [{
            "id": "held-1", "question": question, "reference_answer": answer,
            "evaluation_kind": "UNSEEN_FACT"}]}, ensure_ascii=False), encoding=encoding)

    def test_empty_holdout(self):
        self.source.write_text('{"records":[]}', encoding="utf-8")
        self.assertEqual(inspect(self.source, self.store)["status"], "NOT_READY")

    def test_exact_overlap_detected_with_bom(self):
        self.make("量子センサーとは？", "量子センサーは量子状態を利用して物理量を測定する。",
                  "utf-8-sig")
        result = inspect(self.source, self.store)
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertEqual(result["details"][0]["score"], 1.0)

    def test_paraphrase_like_overlap_flagged(self):
        self.make("量子センサーとは？", "量子センサーは量子状態を利用して物理量を測定する装置。")
        self.assertEqual(inspect(self.source, self.store)["status"], "REVIEW_REQUIRED")

    def test_disjoint_text_is_not_semantic_certificate(self):
        self.make("月の地形は？", "月面には多数のクレーターが存在する。")
        result = inspect(self.source, self.store)
        self.assertEqual(result["status"], "NO_LEXICAL_FLAGS")
        self.assertFalse(result["semantic_independence_verified"])
        self.assertFalse(result["training_exposure_excluded"])

    def test_missing_store_fails_closed(self):
        self.make("質問", "回答")
        self.store.unlink()
        self.assertEqual(inspect(self.source, self.store)["status"], "TRAINING_STORE_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
