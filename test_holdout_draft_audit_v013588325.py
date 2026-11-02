import unittest
from generate_independent_holdout_draft_v013588325 import build
from audit_holdout_draft_v013588325 import audit

class DraftAuditTests(unittest.TestCase):
    def test_draft_is_never_independent(self):
        report = audit(build())
        self.assertEqual(report["status"], "REVIEW_REQUIRED")
        self.assertFalse(report["independence_verified"])
    def test_all_multiturn_cases_need_context(self):
        report = audit(build())
        self.assertEqual(report["flag_counts"]["SINGLE_TURN_IN_MULTI_TURN_CATEGORY"], 10)
    def test_all_cases_need_review(self):
        report = audit(build())
        self.assertEqual(report["flag_counts"]["HUMAN_REVIEW_PENDING"], 50)
    def test_reject_wrong_schema(self):
        with self.assertRaises(ValueError):
            audit({"schema": "bad", "cases": []})
if __name__ == "__main__": unittest.main()
