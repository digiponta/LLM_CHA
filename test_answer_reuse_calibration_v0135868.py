import unittest
from calibrate_answer_reuse_v0135868 import evaluate
class Tests(unittest.TestCase):
 def test_accuracy_and_reject(self):
  def row(q,rank,yes,score):
   return {"query_id":q,"rank":str(rank),"candidate_id":f"{q}-{rank}",
     "answer_reusable":"YES" if yes else "NO","base_score":str(score),
     "adjusted_score":str(score)}
  groups={"known":[row("known",i,i==1,0.95-(i-1)*.01) for i in range(1,11)],
          "unknown":[row("unknown",i,False,0.50-(i-1)*.01) for i in range(1,11)]}
  r=evaluate(groups,.85,0)
  self.assertEqual(r["accepted_count"],1)
  self.assertEqual(r["accepted_answer_accuracy"],1)
  self.assertEqual(r["no_reusable_top10_reject_rate"],1)
 def test_bad_top1(self):
  rows=[{"query_id":"x","rank":str(i),"candidate_id":str(i),
         "answer_reusable":"YES" if i==2 else "NO","base_score":str(.95-i*.01),
         "adjusted_score":str(.95-i*.01)} for i in range(1,11)]
  r=evaluate({"x":rows},.8,0)
  self.assertEqual(r["false_accept_count"],1)
  self.assertEqual(r["accepted_answer_accuracy"],0)
if __name__=="__main__":unittest.main()
