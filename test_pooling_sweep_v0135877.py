import unittest
from pooling_sweep_v0135877 import run_sweep,CONFIGS
class SweepTests(unittest.TestCase):
 def test_configurations_and_metrics(self):
  rows=[{"query_id":"q","candidate_id":"a","query":"hello","candidate_question":"hello","answer_reusable":"true","proposed_label":"KNOWN"},
        {"query_id":"q","candidate_id":"b","query":"hello","candidate_question":"goodbye","answer_reusable":"false","proposed_label":"KNOWN"}]
  def fake(pooling,alpha):
   return lambda x: [1.0,0.0] if x=="hello" else [0.0,1.0]
  r=run_sweep(rows,{"q":"hello"},{"a":"hello","b":"goodbye"},fake)
  self.assertEqual(len(r["configurations"]),len(CONFIGS))
  self.assertEqual(r["configurations"][0]["hit_at_k_eligible"]["1"],1.0)
  self.assertGreater(r["configurations"][0]["mean_margin"],0)
if __name__=="__main__":unittest.main()
