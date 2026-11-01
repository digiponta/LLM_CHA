import unittest
from evaluate_rse_generalization_v013588324 import evaluate,CASES
class GeneralizationEvaluationTests(unittest.TestCase):
 def test_full_fixture_matrix(self):
  report=evaluate()
  self.assertEqual(report["total"],12)
  self.assertEqual(report["status"],"PASS",report["cases"])
  self.assertEqual(report["negative_false_adoptions"],0)
 def test_cases_are_unique(self):
  ids=[x["id"] for x in CASES]
  self.assertEqual(len(ids),len(set(ids)))
 def test_covers_revocation_competition_and_fact(self):
  names={x["id"] for x in CASES}
  self.assertTrue({"revoked-not-selected","two-approved-collision","unrelated-factual"}.issubset(names))
if __name__=="__main__":unittest.main()
