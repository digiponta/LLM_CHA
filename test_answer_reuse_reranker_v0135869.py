import unittest
from rerank_answer_reuse_v0135869 import signals,rank_candidates
class Tests(unittest.TestCase):
 def test_change_vs_continuation(self):
  z=signals("新しい話題に変えたい","その話の続きが聞きたい","詳しく話そう")
  self.assertTrue(z["change_vs_continue"])
 def test_unsupported_specific(self):
  self.assertTrue(signals("この写真の犬種を教えて","犬が好き","そうだね")["unsupported_specific_request"])
 def test_rerank_switch(self):
  candidates=[{"candidate_id":"a","candidate_question":"前の話の続きを話そう","candidate_answer":"続きを話そう","adjusted_score":.92},
              {"candidate_id":"b","candidate_question":"話題を変えよう","candidate_answer":"何の話にしようか","adjusted_score":.91}]
  x=rank_candidates("新しい話題に変えたい",candidates)
  self.assertEqual(x[0]["candidate_id"],"b")
 def test_deterministic(self):
  candidates=[{"candidate_id":"b","candidate_question":"あ","candidate_answer":"そう","adjusted_score":.9},
              {"candidate_id":"a","candidate_question":"あ","candidate_answer":"そう","adjusted_score":.9}]
  self.assertEqual(rank_candidates("い",candidates)[0]["candidate_id"],"a")
if __name__=="__main__":unittest.main()
