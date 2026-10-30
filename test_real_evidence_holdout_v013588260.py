import unittest
from collect_real_evidence_v013588260 import collect
from evaluate_real_evidence_v013588260 import validate_review,evaluate

def fake_fetch(title):
    return {"page_id":42,"title":title,"url":"https://ja.wikipedia.org/wiki/Example",
            "excerpt":"宇宙とは、空間と時間およびその中に含まれるものの全体を指す。"}

class RealEvidenceTests(unittest.TestCase):
    def test_collector_does_not_auto_approve(self):
        data=collect([("宇宙","宇宙とは")],fetch=fake_fetch,when="2026-10-30T00:00:00Z")
        self.assertEqual(data["cases"][0]["review"]["status"],"PENDING_HUMAN_REVIEW")
        self.assertFalse(data["cases"][0]["review"]["source_independent"])
        self.assertEqual(evaluate(data,min_cases=1)["status"],"NOT_READY")
    def test_minimum_size(self):
        data=collect([("宇宙","宇宙とは")],fetch=fake_fetch)
        self.assertIn("INSUFFICIENT_CASES",validate_review(data))
    def test_review_requires_answer_value(self):
        data=collect([("宇宙","宇宙とは")],fetch=fake_fetch)
        review=data["cases"][0]["review"]
        review.update(status="APPROVED_BY_HUMAN",source_independent=True,answerable=True,reviewer_note="Independence checked")
        self.assertIn("ANSWER_VALUE_NOT_ATTESTED",validate_review(data,min_cases=1))
    def test_valid_review_metrics(self):
        data=collect([("宇宙","宇宙とは")],fetch=fake_fetch)
        data["cases"][0]["review"].update(status="APPROVED_BY_HUMAN",source_independent=True,
              answerable=True,required_substring="宇宙とは",reviewer_note="Manually checked source and answer")
        result=evaluate(data,min_cases=1)
        self.assertEqual(result["status"],"HUMAN_REVIEWED_EVIDENCE_DIAGNOSTIC")
        self.assertEqual(result["correct_accept"],1)
        self.assertEqual(result["selective_accuracy"],1.0)
if __name__=="__main__":unittest.main()
