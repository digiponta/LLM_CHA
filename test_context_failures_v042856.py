import unittest
from diagnose_context_failures_v042856 import examine,keywords

class DiagnosticsTests(unittest.TestCase):
 def fixtures(self):
  review={"version":"v0.4.28.52","records":[{"id":"1","question":"人: 映画が好き\n相手: そうですね\n人: 映画を見ますか？","ratings":{"training_suitability":"pass"}}]}
  raw={"version":"v0.4.28.54","results":[{"id":"1","source_line":1,
       "variants":{"full_context":{"status":"generated","response":"映画を見ます。"},
                   "last_user_only":{"status":"generated","response":"そうですね。"}}}]}
  return review,raw
 def test_keyword_overlap(self):
  self.assertIn("映画",keywords("映画を見ます"))
 def test_evaluation_has_no_winner(self):
  a,b=self.fixtures();self.assertIsNone(examine(a,b)["model_quality_winner"])
 def test_counts(self):
  a,b=self.fixtures();d=examine(a,b)
  self.assertEqual(d["count_by_arm"]["last_user_only"]["generic_exact"],1)
 def test_no_approval(self):
  a,b=self.fixtures();self.assertFalse(examine(a,b)["train_ready"])
 def test_unknown_id_rejected(self):
  a,b=self.fixtures();b["results"][0]["id"]="missing"
  with self.assertRaises(ValueError):examine(a,b)
 def test_invalid_status_rejected(self):
  a,b=self.fixtures();b["results"][0]["variants"]["full_context"]["status"]="bad"
  with self.assertRaises(ValueError):examine(a,b)
 def test_blind_review_unrated(self):
  a,b=self.fixtures();r=examine(a,b)
  self.assertIsNone(r["cases"][0]["variants"]["full_context"]["blind_review"]["relevance"])
if __name__=="__main__":unittest.main()
