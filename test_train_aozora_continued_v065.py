import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from train_aozora_continued_v065 import read_corpus, split_by_work, path_guard


def row(work, text):
    return {
        "text": text,
        "train_ready": False,
        "auto_promote": False,
        "provenance": {"work_id": work},
        "natural_language_refs": [{
            "content_hash": "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
        }]
    }


class AozoraTrainingTests(unittest.TestCase):
    def test_no_work_leakage(self):
        train, val, held = split_by_work([("789", "猫"), ("789", "猫2"), ("1567", "メロス")], "1567")
        self.assertEqual(held, "1567")
        self.assertEqual(train, ["猫", "猫2"])
        self.assertEqual(val, ["メロス"])

    def test_one_work_rejected(self):
        with self.assertRaises(ValueError):
            split_by_work([("789", "猫")])

    def test_undocumented_validation_work_rejected(self):
        with self.assertRaises(ValueError):
            split_by_work([("789", "猫"), ("1567", "メロス")], "other")

    def test_verified_corpus(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "corpus.jsonl"
            path.write_text(json.dumps(row("789", "吾輩"), ensure_ascii=False) + "\n", encoding="utf-8")
            self.assertEqual(read_corpus(path), [("789", "吾輩")])

    def test_hash_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "corpus.jsonl"
            record = row("789", "吾輩")
            record["text"] = "別の文章"
            path.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_corpus(path)

    def test_existing_output_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base, output, report = (root / x for x in ("base.pt", "out.pt", "report.json"))
            output.write_bytes(b"existing")
            with self.assertRaises(FileExistsError):
                path_guard(base, output, report)

    def test_same_path_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "same.pt"
            with self.assertRaises(ValueError):
                path_guard(path, path, Path(temp) / "report.json")


if __name__ == "__main__":
    unittest.main()
