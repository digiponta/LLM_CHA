import unittest
from analyze_topic_contrastive_v02292 import rank_candidates,assemble_candidates

class TopicContrastiveTests(unittest.TestCase):
    def test_correct_rank(self):
        r=rank_candidates([("カレー",2.0),("宇宙探査",3.0),("陶芸",4.0)],"カレー")
        self.assertTrue(r["correct_at_1"])
        self.assertEqual(r["correct_rank"],1)
        self.assertAlmostEqual(r["margin_wrong_minus_correct"],1.0)
    def test_wrong_rank(self):
        r=rank_candidates([("カレー",3.0),("宇宙探査",2.0)],"カレー")
        self.assertFalse(r["correct_at_1"])
        self.assertEqual(r["correct_rank"],2)
        self.assertAlmostEqual(r["margin_wrong_minus_correct"],-1.0)
    def test_split_isolation(self):
        rows=[{"split":"train","topic":"A","reference":"Aです"},
              {"split":"holdout","topic":"B","reference":"Bです"}]
        self.assertEqual(assemble_candidates(rows,"holdout"),{"B":["Bです"]})
    def test_invalid_gold(self):
        with self.assertRaises(ValueError):
            rank_candidates([("X",2.0)],"Y")
if __name__=="__main__":unittest.main()
