import tempfile
import unittest
from pathlib import Path
from raw_corpus_evidence_review_v0370 import collect,review

class CorpusEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"source.txt"
        self.path.write_text("量子力学は何だろう。数学について考える。\n量子力学の可能性もある。",encoding="utf-8")
    def tearDown(self):self.tmp.cleanup()
    def test_excerpt_with_line(self):
        rows=collect(self.path,"量子力学")
        self.assertEqual(len(rows),2)
        self.assertEqual([r["line"] for r in rows],[1,2])
    def test_no_automatic_promotion(self):
        doc=review(self.path,"量子力学")
        self.assertEqual(doc["authoritative_propositions_added"],0)
        self.assertFalse(doc["truth_gate_modified"])
        self.assertTrue(all(not r["auto_promoted"] for r in doc["review_candidates"]))
    def test_speculative_markers(self):
        rows=collect(self.path,"量子力学")
        self.assertTrue(rows[1]["speculative"])
    def test_unchanged_source(self):
        before=self.path.read_bytes();collect(self.path,"量子力学")
        self.assertEqual(before,self.path.read_bytes())
    def test_limit(self):
        self.assertEqual(len(collect(self.path,"量子力学",1)),1)
    def test_no_match(self):
        self.assertEqual(collect(self.path,"相対性理論"),[])
    def test_invalid_empty_concept(self):
        with self.assertRaises(ValueError):collect(self.path," ")
    def test_invalid_limit(self):
        with self.assertRaises(ValueError):collect(self.path,"数学",0)
    def test_evidence_id_repeatable(self):
        self.assertEqual(collect(self.path,"量子力学"),collect(self.path,"量子力学"))
if __name__=="__main__":unittest.main()
