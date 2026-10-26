import unittest
from semantic_action_consistency_v09748 import extract,check
class ActionConsistencyTests(unittest.TestCase):
    def test_baguette(self):
        n="ハム&ゴーダチーズ スターバックス バゲットサンド"
        r=check(n+"を食べた","そう、"+n+"を飲んだのね。どんな味だった？")
        self.assertEqual(r.decision,"REPAIR")
        self.assertIn(n+"を食べたのね",r.selected)
    def test_correct_eat(self):
        r=check("ケーキを食べた","ケーキを食べたんだね。")
        self.assertEqual(r.decision,"CONSISTENT")
    def test_negation_preservation(self):
        r=check("ケーキを食べなかった","ケーキを食べたんだね。")
        self.assertEqual(r.decision,"REPAIR")
        self.assertIn("食べなかった",r.selected)
    def test_buy_vs_borrow(self):
        r=check("本を買った","本を借りたのね。")
        self.assertEqual(r.decision,"REPAIR")
        self.assertIn("買った",r.selected)
    def test_see_vs_hear(self):
        r=check("映画を見た","映画を聞いたんだね。")
        self.assertEqual(r.decision,"REPAIR")
    def test_object_guard(self):
        r=check("ケーキを食べた","ラテを飲んだんだね。")
        self.assertEqual(r.decision,"REVIEW")
    def test_ambiguous(self):
        self.assertIsNone(extract("ケーキを食べた。ラテを飲んだ。","USER_UTTERANCE"))
    def test_no_promotion(self):
        r=check("ケーキを食べた","ケーキを飲んだ。")
        self.assertFalse(r.auto_promote or r.train_ready or r.persisted)
if __name__=="__main__":unittest.main()
