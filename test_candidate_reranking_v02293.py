import unittest
from evaluate_candidate_reranking_v02293 import rerank,features
class RerankingTests(unittest.TestCase):
    def test_oracle_candidate(self):
        xs=[{"index":0,"nll":1.1,"topic_mention":False,"generic_exact":True,"repeated_span":False},
            {"index":1,"nll":2.3,"topic_mention":True,"generic_exact":False,"repeated_span":False}]
        self.assertEqual(rerank(xs,"nll")["index"],0)
        self.assertEqual(rerank(xs,"lexical")["index"],1)
    def test_exact_topic(self):
        self.assertTrue(features("宇宙探査","宇宙探査について話す。",2.0)["topic_mention"])
        self.assertFalse(features("宇宙探査","宇宙は広い。",2.0)["topic_mention"])
    def test_empty(self):
        with self.assertRaises(ValueError):rerank([])
    def test_tie_deterministic(self):
        x=[{"index":1,"nll":3.0,"topic_mention":False,"generic_exact":False,"repeated_span":False},
           {"index":0,"nll":3.0,"topic_mention":False,"generic_exact":False,"repeated_span":False}]
        self.assertEqual(rerank(x,"nll")["index"],0)
if __name__=="__main__":unittest.main()
