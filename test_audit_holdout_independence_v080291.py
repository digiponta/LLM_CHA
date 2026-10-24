import json
import tempfile
import unittest
from pathlib import Path
from audit_holdout_independence_v080291 import review

class ResolutionTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        p=Path(self.folder.name)
        self.source=p/"holdout.json"
        self.store=p/"store.json"
        self.reviews=p/"reviews.json"
        self.source.write_text(json.dumps({"records":[{"id":"h1","evaluation_kind":"UNSEEN_FACT",
            "question":"SI基本単位はいくつあるか","reference_answer":"SI基本単位は7つ",
            "source_url":"https://example.org/si","source_excerpt":"seven base units"}]},ensure_ascii=False),encoding="utf-8")
        self.store.write_text(json.dumps({"candidates":[{"id":"t1","subject":"量子ビット",
            "natural_language":"量子ビットは量子情報の基本単位である"}]},ensure_ascii=False),encoding="utf-8")
    def write_review(self,**override):
        record={"id":"h1","source_checked":True,"answer_checked":True,
                "training_nonoverlap_checked":True,"overlap_manually_resolved":True}
        record.update(override)
        self.reviews.write_text(json.dumps({"reviews":[record]}),encoding="utf-8")
    def test_resolved_overlap_no_pending_warning(self):
        self.write_review()
        result=review(self.source,self.store,self.reviews)
        self.assertEqual(result["status"],"MANUAL_REVIEW_RECORDED")
        self.assertEqual(result["findings"][0]["overlap_review_resolution"],"MANUALLY_RESOLVED")
        self.assertTrue(result["findings"][0]["overlap_candidates"])
        self.assertFalse(result["formal_holdout_approved"])
    def test_unresolved_stays_review_required(self):
        self.write_review(overlap_manually_resolved=False)
        self.assertEqual(review(self.source,self.store,self.reviews)["status"],"REVIEW_REQUIRED")
    def test_incomplete_human_review_not_resolved(self):
        self.write_review(training_nonoverlap_checked=False)
        self.assertEqual(review(self.source,self.store,self.reviews)["status"],"REVIEW_REQUIRED")
    def test_missing_review_file_fails_closed(self):
        self.assertEqual(review(self.source,self.store,self.reviews)["review_error"],"REVIEW_FILE_NOT_FOUND")
    def test_no_review_keeps_warning(self):
        self.assertEqual(review(self.source,self.store)["status"],"REVIEW_REQUIRED")
if __name__=="__main__":
    unittest.main()
