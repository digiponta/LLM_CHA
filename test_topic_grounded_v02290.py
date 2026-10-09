import unittest
from prepare_topic_grounded_v02290 import build,TRAIN,HOLDOUT
from evaluate_topic_grounded_v02290 import score

class GroundedFixtureTests(unittest.TestCase):
    def test_disjoint(self):
        self.assertFalse(set(TRAIN)&set(HOLDOUT))
    def test_counts(self):
        rows=build()
        self.assertEqual(sum(r["split"]=="train" for r in rows),12)
        self.assertEqual(sum(r["split"]=="holdout" for r in rows),6)
    def test_no_leak(self):
        with self.assertRaises(ValueError):
            build({"同一話題":["同一話題です"]},{"同一話題":["同一話題について"]})
    def test_topic_metric(self):
        self.assertTrue(score("宇宙探査","宇宙探査を考えよう",8)["topic_mention"])
        self.assertFalse(score("宇宙探査","そうですね。",5)["topic_mention"])
    def test_generic_metric(self):
        self.assertTrue(score("カレー","長門有希。",6)["generic_without_topic"])
if __name__=="__main__":unittest.main()
