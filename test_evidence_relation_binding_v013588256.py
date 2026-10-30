import unittest
from evidence_relation_binding_v013588256 import bind

EV={"status":"EVIDENCE","topic":"宇宙","url":"https://example.test",
"excerpt":"ビッグバンとは、宇宙開始時の爆発的膨張のことである。その時刻は今から138.2億年前と計算されている。20世紀前半までは、天文学者の間でも宇宙は定常的と考えられた。遠方の銀河が観測されるため、宇宙が膨張していると解釈される。"}
class BindingTests(unittest.TestCase):
 def test_big_bang_age_not_history(self):
  r=bind("ビッグバンはいつ起きたのか",EV)
  self.assertEqual(r["status"],"BOUND_EXTRACT_ACCEPTED")
  self.assertIn("138.2億年前",r["value"])
  self.assertNotIn("20世紀",r["sentence"])
 def test_universe_definition_not_big_bang_definition(self):
  self.assertEqual(bind("宇宙とは",EV)["status"],"ABSTAIN_NO_BOUND_EVIDENCE")
 def test_expansion_cause_is_not_expansion_evidence(self):
  self.assertEqual(bind("宇宙はなぜ膨張するのか",EV)["status"],"ABSTAIN_NO_BOUND_EVIDENCE")
 def test_composition_missing(self):
  self.assertEqual(bind("宇宙の化学組成は",EV)["status"],"ABSTAIN_NO_BOUND_EVIDENCE")
 def test_big_bang_definition(self):
  self.assertEqual(bind("ビッグバンとは",EV)["status"],"BOUND_EXTRACT_ACCEPTED")
 def test_missing_source(self):
  self.assertEqual(bind("ビッグバンとは",{"status":"NO_EVIDENCE"})["status"],"ABSTAIN_NO_EVIDENCE")
if __name__=="__main__": unittest.main()
