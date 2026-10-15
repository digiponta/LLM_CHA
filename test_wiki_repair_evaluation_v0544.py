import json
import unittest
from pathlib import Path
from evaluate_wiki_repair_v0544 import evaluate_cases
ROOT=Path(__file__).parent
CASES=json.loads((ROOT/"data"/"wiki_repair_eval_v0543.json").read_text(encoding="utf-8"))["cases"]
class WikiEvaluationV0544Tests(unittest.TestCase):
 def test_counts(self):
  n=evaluate_cases(CASES)["counts"]
  self.assertEqual((n["total"],n["need"],n["no_need"]),(6,4,2))
 def test_confusion_matrix(self):
  n=evaluate_cases(CASES)["counts"]
  self.assertEqual((n["tp"],n["fp"],n["tn"],n["fn"]),(3,0,2,1))
 def test_availability(self):
  n=evaluate_cases(CASES)["counts"]
  self.assertEqual((n["need_with_evidence"],n["need_without_evidence"]),(3,1))
 def test_precision_recall(self):
  m=evaluate_cases(CASES)["metrics"]
  self.assertEqual(m["suggestion_precision"],1.0)
  self.assertEqual(m["suggestion_recall"],0.75)
 def test_render_success(self):
  m=evaluate_cases(CASES)["metrics"]
  self.assertEqual(m["render_success_given_evidence"],1.0)
  self.assertEqual(m["evidence_preservation_rate"],1.0)
 def test_continuity_proxy(self):
  m=evaluate_cases(CASES)["metrics"]
  self.assertEqual(m["conversation_continuity_proxy"],round(2/3,4))
 def test_unknown(self):
  n=evaluate_cases(CASES)["counts"]
  self.assertEqual((n["unknown_need"],n["unknown_recovered"]),(2,1))
 def test_not_needed_excluded(self):
  n=evaluate_cases(CASES)["counts"]
  self.assertEqual(n["need_with_evidence"]+n["need_without_evidence"],n["need"])
 def test_no_denominator(self):
  r=evaluate_cases([])
  self.assertIsNone(r["metrics"]["suggestion_precision"])
  self.assertIsNone(r["metrics"]["render_success_given_evidence"])
 def test_no_truth_claim(self):
  r=evaluate_cases(CASES)
  self.assertFalse(r["external_verification"]);self.assertFalse(r["train_ready"])
if __name__=="__main__":unittest.main()
