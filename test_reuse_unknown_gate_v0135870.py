import unittest
from evaluate_reuse_unknown_gate_v0135870 import choose,evaluate
class Tests(unittest.TestCase):
 def candidate(self,id,q,score,correct,rank):
  return {"query_id":"q","query":q,"rank":str(rank),"candidate_id":id,
      "candidate_question":"その話の続きが聞きたい" if id=="wrong" else "話題を変えたい",
      "candidate_answer":"続きを聞きたい" if id=="wrong" else "何の話にしようか",
      "base_score":str(score),"adjusted_score":str(score),
      "answer_reusable":"YES" if correct else "NO"}
 def test_rerank_corrects_topic(self):
  rows=[self.candidate("wrong","新しい話題に変えたい",.92,False,1),
        self.candidate("right","新しい話題に変えたい",.91,True,2)]
  d=choose(rows,"reuse_reranked",.85,0)
  self.assertEqual(d["candidate_id"],"right")
  self.assertTrue(d["top1_reusable_for_evaluation"])
 def test_unknown_rejected(self):
  rows=[self.candidate("wrong","新しい話題に変えたい",.4,False,1),
        self.candidate("right","新しい話題に変えたい",.3,False,2)]
  d=choose(rows,"reuse_reranked",.88,0)
  self.assertFalse(d["accepted"])
 def test_gate_metrics(self):
  rows=[self.candidate("wrong","新しい話題に変えたい",.4,False,1),
        self.candidate("right","新しい話題に変えたい",.3,False,2)]
  out=evaluate({"unknown":rows},"baseline",.88,0)
  self.assertEqual(out["nonviable_reject_rate"],1)
  self.assertIsNone(out["accepted_answer_accuracy"])
if __name__=="__main__":unittest.main()
