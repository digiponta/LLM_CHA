import unittest
from evaluate_rse_gate_v013588306 import measure
class GateBenchmarkTests(unittest.TestCase):
 def test_counts_and_abstentions(self):
  cases=[
   {"id":"a","query":"最近どう？","source_question":"元気ですかー？","source_answer":"元気ですよー！","suitable":False},
   {"id":"b","query":"少し話さない？","source_question":"少し話さない？","source_answer":"もちろん、話そう。","suitable":True}
  ]
  x=measure(cases)
  self.assertEqual(x["true_reject"],1)
  self.assertEqual(x["review_positive"],1)
  self.assertEqual(x["false_reject"],0)
  self.assertTrue(x["no_auto_accept_path"])
 def test_labels_required(self):
  with self.assertRaises(ValueError):
   measure([{"id":"x","query":"a","source_question":"a","source_answer":"b"}])
if __name__=="__main__":unittest.main()
