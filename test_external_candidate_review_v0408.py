import json
import tempfile
import unittest
from pathlib import Path
from external_candidate_store_v0407 import ingest
from external_candidate_review_v0408 import review, list_candidates
from test_external_candidate_store_v0407 import report

class ExternalCandidateReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.input=Path(self.temp.name)/"input.json"
        self.store=Path(self.temp.name)/"store.json"
        self.input.write_text(json.dumps(report(),ensure_ascii=False),encoding="utf-8")
        ingest(self.input,self.store)
        self.item=list_candidates(self.store)[0]
    def tearDown(self):self.temp.cleanup()
    def apply(self,decision="APPROVED_FOR_REVIEW_ONLY",sha=None,reason="出典を確認した。"):
        return review(self.store,self.item["id"],sha or self.item["content_sha256"],
                      decision,"local-reviewer",reason)
    def test_list(self):
        self.assertEqual(len(list_candidates(self.store)),1)
    def test_approve_not_training(self):
        x=self.apply()
        self.assertEqual(x["review_state"],"APPROVED_FOR_REVIEW_ONLY")
        self.assertEqual(x["truth_promotions"],0)
        self.assertFalse(x["training_enabled"])
        row=json.loads(self.store.read_text(encoding="utf-8"))["records"][0]
        self.assertEqual(row["factual_truth"],"UNVERIFIED")
        self.assertFalse(row["eligible_for_training"])
    def test_reject(self):
        self.assertEqual(self.apply("REJECTED")["review_state"],"REJECTED")
    def test_pending(self):
        self.apply("REJECTED")
        self.assertEqual(self.apply("PENDING_REVIEW")["review_state"],"PENDING_REVIEW")
    def test_audit(self):
        self.apply()
        self.apply("REJECTED")
        d=json.loads(self.store.read_text(encoding="utf-8"))["records"][0]
        self.assertEqual(len(d["review_audit"]),2)
        self.assertEqual(d["review_audit"][1]["previous_state"],"APPROVED_FOR_REVIEW_ONLY")
        self.assertEqual(d["review_audit"][1]["article_url"],self.item["url"])
    def test_stale_sha_rejected_unchanged(self):
        before=self.store.read_bytes()
        with self.assertRaises(ValueError):self.apply(sha="0"*64)
        self.assertEqual(before,self.store.read_bytes())
    def test_invalid_reviewer(self):
        with self.assertRaises(ValueError):
            review(self.store,self.item["id"],self.item["content_sha256"],
                   "REJECTED","","some reason")
    def test_invalid_decision(self):
        with self.assertRaises(ValueError):self.apply("TRUE")
    def test_missing_candidate(self):
        with self.assertRaises(ValueError):
            review(self.store,"0"*24,self.item["content_sha256"],"REJECTED","r","reason")
    def test_updated_source_forces_rereview(self):
        self.apply()
        self.input.write_text(json.dumps(report("更新"),ensure_ascii=False),encoding="utf-8")
        ingest(self.input,self.store)
        d=json.loads(self.store.read_text(encoding="utf-8"))["records"][0]
        self.assertEqual(d["review_state"],"NEEDS_REREVIEW")
        self.assertEqual(len(d["review_audit"]),1)
        before=self.store.read_bytes()
        with self.assertRaises(ValueError):self.apply()
        self.assertEqual(before,self.store.read_bytes())
if __name__=="__main__":unittest.main()
