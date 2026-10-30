import unittest
from response_correlation_v013588235 import response_action

class ResponseCorrelationTests(unittest.TestCase):
 def test_orphan_unknown_suppressed(self):
  self.assertEqual(response_action("","未学習です"),"SUPPRESS_UNCORRELATED")
 def test_orphan_nonunknown_suppressed(self):
  self.assertEqual(response_action("","追加の回答"),"SUPPRESS_UNCORRELATED")
 def test_grounded_answer(self):
  self.assertEqual(response_action("資料を使って宇宙を説明","生成結果",True),"EVALUATE_EVIDENCE")
 def test_regular_answer(self):
  self.assertEqual(response_action("CPUとは","中央処理装置"),"ROUTE_NORMAL")
if __name__=="__main__":unittest.main()
