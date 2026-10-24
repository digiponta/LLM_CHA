import json
import tempfile
import unittest
from pathlib import Path
from audit_holdout_independence_v08027 import review

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p = Path(self.tmp.name)
        self.src, self.store, self.rev = p/"holdout.json", p/"store.json", p/"review.json"
        self.store.write_text(json.dumps({"candidates": [{"id": "t1", "subject": "金星",
            "natural_language": "金星の自転周期は243日である"}]}, ensure_ascii=False), encoding="utf-8")
    def put(self, records):
        self.src.write_text(json.dumps({"records": records}, ensure_ascii=False), encoding="utf-8-sig")
    def record(self, id="h1", q="金星の自転周期は何日か"):
        return {"id": id, "evaluation_kind": "UNSEEN_FACT", "question": q,
                "reference_answer": "243日", "source_url": "https://example.org/source",
                "source_excerpt": "243 days"}
    def test_empty(self):
        self.put([])
        self.assertEqual(review(self.src, self.store)["status"], "NOT_READY")
    def test_overlap(self):
        self.put([self.record()])
        out = review(self.src, self.store)
        self.assertIn("POSSIBLE_SEMANTIC_OR_LEXICAL_OVERLAP", out["findings"][0]["flags"])
        self.assertFalse(out["semantic_independence_verified"])
    def test_missing_provenance(self):
        row = self.record()
        del row["source_excerpt"]
        self.put([row])
        self.assertIn("MISSING_SOURCE_EXCERPT", review(self.src, self.store)["findings"][0]["flags"])
    def test_review_is_not_approval(self):
        self.put([self.record(q="海底地形の測量方法は何ですか")])
        self.rev.write_text(json.dumps({"reviews": [{"id": "h1", "source_checked": True,
            "answer_checked": True, "training_nonoverlap_checked": True}]}), encoding="utf-8")
        out = review(self.src, self.store, self.rev)
        self.assertFalse(out["formal_holdout_approved"])
        self.assertFalse(out["written"])
    def test_missing_store_fails_closed(self):
        self.put([self.record()])
        self.store.unlink()
        self.assertEqual(review(self.src, self.store)["status"], "TRAINING_STORE_NOT_FOUND")

if __name__ == "__main__":
    unittest.main()
