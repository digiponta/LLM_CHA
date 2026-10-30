import unittest
from evidence_definition_anaphora_v013588257 import bind
BASE={"status":"EVIDENCE","topic":"宇宙","url":"https://example.test","excerpt":"ビッグバンとは、宇宙開始時の爆発的膨張のことである。その時刻は今から138.2億年（13.82 × 109年）前と計算されている。20世紀前半までは、天文学者の間でも「宇宙は不変で定常的」という考え方が支配的だった。"}
class BindingTests(unittest.TestCase):
 def test_universe_definition_abstains_on_history(self):
  self.assertEqual(bind("宇宙とは",BASE)["status"],"ABSTAIN_NO_BOUND_EVIDENCE")
 def test_big_bang_age_antecedent(self):
  result=bind("ビッグバンはいつ起きたのか",BASE)
  self.assertEqual(result["status"],"BOUND_EXTRACT_ACCEPTED")
  self.assertIn("138.2億年",result["value"])
  self.assertTrue(result["value"].endswith("前"))
 def test_anaphora_without_antecedent_abstains(self):
  ev={**BASE,"excerpt":"この論文では年代を論じている。その時刻は今から138.2億年前と計算された。"}
  self.assertEqual(bind("ビッグバンはいつ起きたのか",ev)["status"],"ABSTAIN_NO_BOUND_EVIDENCE")
 def test_real_universe_definition(self):
  ev={**BASE,"excerpt":"宇宙とは、すべての空間と時間およびそこに存在する物質とエネルギーの全体を指す。"}
  self.assertEqual(bind("宇宙とは",ev)["status"],"BOUND_EXTRACT_ACCEPTED")
 def test_cause_abstains(self):
  self.assertEqual(bind("宇宙はなぜ膨張するのか",BASE)["status"],"ABSTAIN_NO_BOUND_EVIDENCE")
 def test_big_bang_definition_preserved(self):
  self.assertEqual(bind("ビッグバンとは",BASE)["status"],"BOUND_EXTRACT_ACCEPTED")
if __name__=="__main__":unittest.main()
