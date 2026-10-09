import unittest
from types import SimpleNamespace
from candidate_reranker_v0220 import rank_candidates

def item(text,conf=.6):
    return SimpleNamespace(text=text,mean_confidence=conf,min_confidence=.15,mean_top2_margin=.2)
class CandidateRerankerTests(unittest.TestCase):
    def test_substantive_sf_candidate_wins(self):
        xs=[item("そう。"),item("SF小説なんだ。どんな作品を読んでいるの？")]
        ranked,scores=rank_candidates("最近、SF小説を読んでいます",xs,[])
        self.assertEqual(ranked[0].text,xs[1].text)
        self.assertTrue(scores[0]["acknowledgement"])
    def test_quality_and_confidence_still_required(self):
        xs=[item("SF小説についてもっと話して。",conf=.01),item("そう。")]
        ranked,scores=rank_candidates("最近、SF小説を読んでいます",xs,[],min_confidence=.18)
        self.assertFalse(scores[0]["valid"])
        self.assertEqual(ranked[0].text,"そう。")
    def test_stable_tie_favors_greedy(self):
        xs=[item("どんな小説を読んでいるの？"),item("どんな小説を読んでいるの？")]
        ranked,_=rank_candidates("最近小説を読んでいます",xs,[])
        self.assertIs(ranked[0],xs[0])
    def test_no_candidate(self):
        self.assertEqual(rank_candidates("こんにちは",[],[]),([],[]))
if __name__=="__main__":unittest.main()
