import tempfile
import unittest
from pathlib import Path
from raw_concept_evidence_v0615 import find_mentions,present_mentions,normalize_focus

class NonSubjectEvidenceTests(unittest.TestCase):
    def test_non_subject_term(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"text.txt"
            p.write_text("物体の運動は時間に依存する。\n空間は広がっている。\n",encoding="utf-8")
            hits=find_mentions(p,"時間")
            self.assertEqual(len(hits),1)
            self.assertEqual(hits[0]["line"],1)
            self.assertIn("時間に依存",present_mentions(hits))
            self.assertEqual(hits[0]["truth_state"],"UNVERIFIED")
    def test_not_found(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"text.txt";p.write_text("猫は動物。",encoding="utf-8")
            self.assertEqual(find_mentions(p,"時間"),[])
    def test_command_not_a_concept(self):
        self.assertIsNone(normalize_focus("/sleep"))
    def test_missing_file(self):
        self.assertEqual(find_mentions("does-not-exist.txt","時間"),[])
    def test_limit(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"text.txt";p.write_text("時間の概念は難しい。\n"*10,encoding="utf-8")
            self.assertEqual(len(find_mentions(p,"時間",max_results=2)),2)
if __name__=="__main__":unittest.main()
