import json
import tempfile
import unittest
from pathlib import Path
from proposition_review_v0233828 import apply_review
from proposition_truth_v0233827 import TruthOverlay, proposition_id

class ReviewLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"review.jsonl"
        self.a=proposition_id("宇宙","A","corpus")
        self.b=proposition_id("宇宙","B","corpus")
        self.c=proposition_id("宇宙","C","corpus")

    def review(self,pid,state):
        apply_review(self.path,pid,state,"manual:test-evidence","tester","reviewed test fixture")

    def test_mixed_true_false_unverified(self):
        self.review(self.a,"TRUE")
        self.review(self.b,"FALSE")
        overlay=TruthOverlay(str(self.path))
        self.assertTrue(overlay.decide("宇宙","A","corpus","UNVERIFIED",True).allowed)
        self.assertFalse(overlay.decide("宇宙","B","corpus","UNVERIFIED",True).allowed)
        self.assertEqual(overlay.decide("宇宙","C","corpus","UNVERIFIED",True).state,"UNVERIFIED")

    def test_subject_false_still_blocks_true(self):
        self.review(self.a,"TRUE")
        self.assertFalse(TruthOverlay(str(self.path)).decide("宇宙","A","corpus","FALSE",False).allowed)

    def test_review_metadata_present(self):
        self.review(self.a,"UNVERIFIED")
        row=json.loads(self.path.read_text(encoding="utf-8"))
        self.assertTrue(all(row.get(k) for k in ("reviewer","reason","reviewed_at","provenance")))

    def test_requires_evidence(self):
        with self.assertRaises(ValueError):
            apply_review(self.path,self.a,"TRUE","","tester","review")
        self.assertFalse(self.path.exists())

    def test_invalid_id(self):
        with self.assertRaises(ValueError):
            self.review("bad","TRUE")

    def test_conflict_rejected_without_mutation(self):
        self.review(self.a,"FALSE")
        original=self.path.read_bytes()
        with self.assertRaises(ValueError):
            self.review(self.a,"TRUE")
        self.assertEqual(self.path.read_bytes(),original)

    def test_idempotent_review(self):
        self.review(self.a,"TRUE")
        self.review(self.a,"TRUE")
        self.assertEqual(len(self.path.read_text(encoding="utf-8").splitlines()),1)

    def test_existing_corrupt_file_preserved(self):
        self.path.write_text("not json\n",encoding="utf-8")
        original=self.path.read_bytes()
        with self.assertRaises(ValueError):
            self.review(self.a,"TRUE")
        self.assertEqual(self.path.read_bytes(),original)

    def test_corpus_untouched(self):
        corpus=Path(self.tmp.name)/"corpus.jsonl"
        corpus.write_text("original",encoding="utf-8")
        self.review(self.a,"FALSE")
        self.assertEqual(corpus.read_text(encoding="utf-8"),"original")

if __name__ == "__main__":
    unittest.main()
