import tempfile
import unittest
from pathlib import Path
from expand_foundation_v013584 import build

class FoundationExpansionTests(unittest.TestCase):
    def test_combined_sources(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);a=root/"a.txt";b=root/"b.txt"
            a.write_text("第一文\n第二文\n",encoding="utf-8")
            b.write_text("第二文\n第三文\n",encoding="utf-8")
            rows,report=build([a,b],[],minimum=3)
            self.assertEqual(len(rows),3)
            self.assertEqual(report["status"],"CANDIDATE_READY")
    def test_reserved_exclusion(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);a=root/"a.txt";v=root/"reserve.txt"
            a.write_text("第一文\n第二文\n",encoding="utf-8")
            v.write_text("第一文\n",encoding="utf-8")
            rows,report=build([a],[v],minimum=2)
            self.assertEqual(rows,["第二文"])
            self.assertEqual(report["status"],"INSUFFICIENT_FOUNDATION")
    def test_holdout_source_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"holdout.txt";p.write_text("秘密",encoding="utf-8")
            with self.assertRaises(ValueError):build([p],[])
    def test_duplicate_path_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"a.txt";p.write_text("文章",encoding="utf-8")
            with self.assertRaises(ValueError):build([p,p],[])
    def test_no_auto_approval(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"a.txt";p.write_text("文章",encoding="utf-8")
            _,report=build([p],[],minimum=1)
            self.assertFalse(report["training_approved"])

if __name__=="__main__":
    unittest.main()
