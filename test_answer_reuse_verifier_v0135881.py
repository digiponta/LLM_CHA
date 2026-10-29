import unittest
from answer_reuse_verifier_v0135881 import decide,evaluate
class VerifierTests(unittest.TestCase):
 def row(self,**kw):
  r={"query":"こんにちは","candidate_question":"こんにちは","candidate_answer":"こんにちは。","score":"1.0","source_id":"reviewed-source"}
  r.update(kw);return r
 def test_approved_exact(self):
  self.assertEqual(decide(self.row(),{"reviewed-source"})[0],"ACCEPT")
 def test_unapproved(self):
  self.assertEqual(decide(self.row(),set())[0],"REVIEW")
 def test_nonexact(self):
  self.assertEqual(decide(self.row(query="こんばんは"),{"reviewed-source"})[0],"REVIEW")
 def test_current_info_no_accept(self):
  self.assertEqual(decide(self.row(query="今日の天気",candidate_question="今日の天気"),{"reviewed-source"})[0],"REVIEW")
 def test_label_does_not_change_decision(self):
  a=decide(self.row(answer_reusable="true"),{"reviewed-source"})
  b=decide(self.row(answer_reusable="false"),{"reviewed-source"})
  self.assertEqual(a,b)
 def test_missing_answer_rejected(self):
  self.assertEqual(decide(self.row(candidate_answer=""),{"reviewed-source"})[0],"REJECT")
 def test_invalid_score(self):
  self.assertEqual(decide(self.row(score="nan"),{"reviewed-source"})[0],"REJECT")
 def test_eval(self):
  result=evaluate([self.row(answer_reusable="false")],set())
  self.assertEqual(result["counts"].get("ACCEPT",0),0)
if __name__=="__main__":unittest.main()
