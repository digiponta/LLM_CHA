import unittest
from generate_independent_holdout_draft_v013588325 import build
from prepare_holdout_review_pack_v013588325 import prepare
from audit_holdout_draft_v013588325 import audit

class DevelopmentReviewPackTests(unittest.TestCase):
    def test_50_cases_remain_pending(self):
        out = prepare(build())
        self.assertEqual(len(out["cases"]), 50)
        self.assertTrue(all(c["review_state"] == "PENDING" and c["expected_decision"] is None for c in out["cases"]))
        self.assertFalse(out["independence"]["human_attested"])
    def test_all_multiturn_have_context(self):
        out = prepare(build())
        report = audit(out)
        self.assertNotIn("SINGLE_TURN_IN_MULTI_TURN_CATEGORY", report["flag_counts"])
        self.assertEqual(report["flag_counts"]["HUMAN_REVIEW_PENDING"], 50)
    def test_original_unchanged(self):
        orig = build()
        prepare(orig)
        self.assertEqual(len(orig["cases"][30]["turns"]), 1)
    def test_suggestion_not_approval(self):
        out = prepare(build())
        self.assertEqual(out["cases"][0]["suggested_decision"], "ADOPT")
        self.assertIsNone(out["cases"][0]["expected_decision"])
if __name__ == "__main__": unittest.main()
