import unittest
from hybrid_retrieval_v0135878 import grams,lexical_scores,minmax_by_query,sweep
class HybridTests(unittest.TestCase):
 def test_grams(self):self.assertEqual(grams("abc")["ab"],1)
 def test_lexical(self):
  r=lexical_scores({"q":"猫が好き"},{"a":"猫が好き","b":"半導体回路"})
  self.assertGreater(r[("q","a")],r[("q","b")])
 def test_normalize(self):
  r=minmax_by_query({("q","a"):2,("q","b"):4})
  self.assertEqual(r[("q","a")],0.)
  self.assertEqual(r[("q","b")],1.)
 def test_sweep(self):
  rows=[dict(query_id="q",candidate_id=c,answer_reusable=str(c=="a").lower(),proposed_label="KNOWN") for c in ("a","b")]
  a={("q","a"):1.,("q","b"):0.}
  result=sweep(rows,a,a)
  self.assertEqual(len(result["configurations"]),5)
  self.assertEqual(result["configurations"][0]["hit_at_k_eligible"]["1"],1.)
if __name__=="__main__":unittest.main()
