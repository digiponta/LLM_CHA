import unittest
from diagnose_semantic_retrieval_v0135876 import diagnose
class DiagnosticsTests(unittest.TestCase):
 def test_separation(self):
  reviews=[{"query_id":"q","candidate_id":c,"answer_reusable":str(v).lower(),"proposed_label":"KNOWN","query":"Q"} for c,v in [("a",True),("b",False)]]
  scores=[{"query_id":"q","candidate_id":c,"score":str(s)} for c,s in [("a",0.8),("b",0.3)]]
  r=diagnose(reviews,scores)
  self.assertEqual(r["positive_beats_all_negative_queries"],1)
  self.assertEqual(r["cases"][0]["first_positive_rank"],1)
  self.assertAlmostEqual(r["per_query_margin"]["mean"],0.5)
 def test_missing_pair_fails(self):
  reviews=[{"query_id":"q","candidate_id":"a","answer_reusable":"true","proposed_label":"KNOWN"}]
  with self.assertRaises(ValueError):diagnose(reviews,[])
if __name__=="__main__":unittest.main()
