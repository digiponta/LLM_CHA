import unittest
from diagnose_rse_shadow_v013588311 import analyze
class DiagnosticsTests(unittest.TestCase):
 def report(self):
  return {"status":"AI_PROVISIONAL_SHADOW_EVALUATION","cases":3,"rows":[
   {"id":"a","ai_provisional_suitable":True,"decision":"MANUAL_REVIEW_REQUIRED","reasons":["INTENT_NOT_APPROVED_FOR_CANDIDATE"]},
   {"id":"b","ai_provisional_suitable":False,"decision":"REJECT","reasons":["SELF_REPORT_RISK"]},
   {"id":"c","ai_provisional_suitable":False,"decision":"MANUAL_REVIEW_REQUIRED","reasons":["INTENT_NOT_APPROVED_FOR_CANDIDATE"]}
  ]}
 def test_reason_counts(self):
  x=analyze(self.report())
  self.assertEqual(x["reason_counts"]["INTENT_NOT_APPROVED_FOR_CANDIDATE"],2)
  self.assertEqual(x["decision_counts"]["MANUAL_REVIEW_REQUIRED"],2)
  self.assertEqual(x["by_label"]["provisional_positive"]["MANUAL_REVIEW_REQUIRED"],1)
  self.assertTrue(x["no_test_threshold_tuning"])
 def test_missing_row_fails(self):
  r=self.report();r["rows"].pop()
  with self.assertRaises(ValueError):analyze(r)
 def test_wrong_status_fails(self):
  r=self.report();r["status"]="LABELING_COMPLETE"
  with self.assertRaises(ValueError):analyze(r)
if __name__=="__main__":unittest.main()
