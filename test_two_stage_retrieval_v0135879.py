import unittest
from two_stage_retrieval_v0135879 import run
class TwoStageTests(unittest.TestCase):
 def setUp(self):
  self.rows=[
   {"query_id":q,"candidate_id":c,"answer_reusable":str(ok).lower()}
   for q,c,ok in [("q1","a",True),("q1","b",False),("q2","a",False),("q2","b",False)]]
  self.lex={("q1","a"):1,("q1","b"):0,("q2","a"):1,("q2","b"):0}
  self.sem=dict(self.lex)
 def test_recall_and_abstain(self):
  result=run(self.rows,self.lex,self.sem,ks=(1,),lambdas=(1,),thresholds=(0.5,1.0))
  first=result["configurations"][0]
  self.assertEqual(first["stage1_recall_eligible"],1)
  self.assertEqual(first["accepted_correct"],1)
  self.assertEqual(first["accepted_incorrect"],1)
  self.assertEqual(first["false_accept_rate_no_positive"],1)
 def test_reject_unscored(self):
  with self.assertRaises(ValueError):run(self.rows,{},self.sem)
 def test_reject_invalid_weight(self):
  with self.assertRaises(ValueError):run(self.rows,self.lex,self.sem,lambdas=(2,))
if __name__=="__main__":unittest.main()
