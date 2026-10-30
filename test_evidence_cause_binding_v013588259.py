import json
import unittest
from pathlib import Path
from evidence_cause_binding_v013588259 import bind,cause_value
from evaluate_cause_binding_v013588259 import evaluate

class CauseBindingTests(unittest.TestCase):
 def test_explicit_cause(self):
  ev={"status":"EVIDENCE","topic":"宇宙","url":"https://example.test",
      "excerpt":"宇宙の膨張の原因は、時空のダイナミクスによると説明される。"}
  r=bind("宇宙はなぜ膨張するのか",ev)
  self.assertEqual(r["status"],"BOUND_EXTRACT_ACCEPTED")
  self.assertIn("時空のダイナミクス",r["value"])
 def test_result_not_cause(self):
  self.assertIsNone(cause_value("宇宙の膨張によって密度が低下する。","宇宙はなぜ膨張するのか"))
 def test_other_subject_not_cause(self):
  self.assertIsNone(cause_value("銀河形成の原因は、重力によると説明される。","宇宙はなぜ膨張するのか"))
 def test_no_cause_answer_for_definition(self):
  ev={"status":"EVIDENCE","topic":"宇宙","excerpt":"宇宙とは、すべての空間と時間の全体を指す。"}
  self.assertEqual(bind("宇宙とは",ev)["status"],"BOUND_EXTRACT_ACCEPTED")
 def test_twelve_fixture_metrics(self):
  cases=json.loads(Path("data/independent_binding_eval_v013588258.json").read_text(encoding="utf-8"))["cases"]
  r=evaluate(cases)
  self.assertEqual(r["cases"],12)
  self.assertEqual(r["correct_accept"],5)
  self.assertEqual(r["false_accept"],0)
  self.assertEqual(r["false_negative"],0)
if __name__=="__main__": unittest.main()
