import unittest
from evaluate_rpc_response_ranking_v01340 import ranking_score, rank_candidates

class ResponseRankingTests(unittest.TestCase):
    def test_empty_disallowed(self):
        self.assertLess(ranking_score(0,0,False,True,False),-10000)
    def test_repetition_penalty(self):
        self.assertGreater(ranking_score(3,0,False,False,False),ranking_score(3,.5,False,False,False))
    def test_generic_penalty(self):
        self.assertGreater(ranking_score(3,0,False,False,False),ranking_score(3,0,True,False,False))
    def test_rank_deterministic(self):
        arr=[{"rank_score":-4,"index":0},{"rank_score":-3,"index":1},{"rank_score":-3,"index":2}]
        self.assertEqual(rank_candidates(arr)["index"],1)

if __name__=="__main__":unittest.main()
