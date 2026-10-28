import tempfile
import unittest
from pathlib import Path
from acquire_foundation_v013585 import collect

class AcquisitionTests(unittest.TestCase):
    def test_good_source(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"train.txt"
            p.write_text("日本語の文章を学ぶための独立した練習素材です。\n",encoding="utf-8")
            rows,a=collect([p],[])
            self.assertEqual(len(rows),1)
            self.assertFalse(a["training_approved"])
    def test_reserved_exact(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"train.txt";v=Path(d)/"reserved.txt"
            sentence="日本語の文章を学ぶための独立した練習素材です。"
            p.write_text(sentence,encoding="utf-8");v.write_text(sentence,encoding="utf-8")
            rows,a=collect([p],[v])
            self.assertEqual(rows,[])
            self.assertEqual(a["source_audit"][0]["reserved_exact"],1)
    def test_short_removed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"train.txt";p.write_text("短文\n",encoding="utf-8")
            rows,a=collect([p],[])
            self.assertEqual(rows,[])
    def test_holdout_as_source_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"my_holdout.txt";p.write_text("文章を扱います。",encoding="utf-8")
            with self.assertRaises(ValueError):collect([p],[])
    def test_repeated_path_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"train.txt";p.write_text("これは独立した文章として保持するものです。",encoding="utf-8")
            with self.assertRaises(ValueError):collect([p,p],[])
if __name__=="__main__":unittest.main()
