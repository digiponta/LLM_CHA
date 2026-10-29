import unittest
from evaluate_question_retrieval_v0135862 import rank_nonzero,evaluate
class Tests(unittest.TestCase):
 def setUp(self):
  self.train=[{"id":"a","user":"今日は眠い","assistant":"休んで"},{"id":"b","user":"本を読む","assistant":"いいね"},{"id":"c","user":"雨が降る","assistant":"そう"}]
 def test_no_zero_candidates(self):
  self.assertEqual(rank_nonzero(self.train,"XYZ",ngram=3),[])
 def test_top1_and_unknown(self):
  qs=[{"id":"x","user":"今日は眠い"},{"id":"y","user":"XYZ"}]
  report=evaluate(self.train,qs,{"x":{"a"},"y":set()},ngram=3)
  self.assertEqual(report["top1_accuracy"],1)
  self.assertEqual(report["recall_at_3"],1)
  self.assertEqual(report["unknown_reject_rate"],1)
 def test_invalid_gold(self):
  with self.assertRaises(ValueError):evaluate(self.train,[{"id":"x","user":"本"}],{"x":{"missing"}})
 def test_unlabeled(self):
  with self.assertRaises(ValueError):evaluate(self.train,[{"id":"x","user":"本"}],{})
if __name__=="__main__":unittest.main()
