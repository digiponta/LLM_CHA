import unittest
from dataclasses import dataclass
from candidate_reranker_v0210 import rank_candidates

@dataclass
class Result:
    text:str
    mean_confidence:float=.6
    min_confidence:float=.1
    mean_top2_margin:float=.1

class CandidateRankingTests(unittest.TestCase):
    def setUp(self):
        self.history=[("最近、小説にはまっています","そう。どんな本を読んでいるの?")]
    def test_selects_new_substantive_reply(self):
        a=[Result("そう。どんな本を読んでいるのですね"),Result("SF小説では宇宙探査の物語がよく描かれます。")]
        ordered,scores=rank_candidates("SFです",a,self.history)
        self.assertEqual(ordered[0].text,a[1].text)
        self.assertTrue(scores[0]["repetition"])
    def test_generic_continuation_not_selected(self):
        a=[Result("そうですね。"),Result("SFでは架空の未来社会を描く作品もあります。")]
        ordered,_=rank_candidates("その話、続けて",a,self.history)
        self.assertEqual(ordered[0],a[1])
    def test_no_candidate_can_bypass_downstream_gate(self):
        a=[Result("そうですね。"),Result("未確認の記述",min_confidence=.001)]
        ordered,scores=rank_candidates("その話、続けて",a,self.history)
        self.assertEqual(ordered[0],a[0])
        self.assertFalse(any(x["valid"] for x in scores))
    def test_empty(self):
        self.assertEqual(rank_candidates("SFです",[],self.history),([],[]))
if __name__=="__main__":unittest.main()
