import unittest
from evaluate_semantic_retention_v0100 import summarize

class RetentionSummaryTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(summarize([]),{"evaluated":0,"mean_answer_nll":None})
    def test_ignores_unavailable(self):
        self.assertEqual(summarize([1.0,None,3.0]),{"evaluated":2,"mean_answer_nll":2.0})
    def test_zero(self):
        self.assertEqual(summarize([0.0])["mean_answer_nll"],0.0)

if __name__=="__main__":unittest.main()
