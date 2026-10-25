import unittest
from types import SimpleNamespace
from daily_conversation_foundation_v09728 import dataset
from evaluate_daily_generalization_v09731 import EXTRA,assess,evaluate
class M:
    vocab_size=100
class T:
    vocab_size=100
class EvalTests(unittest.TestCase):
    def test_all_holdout_and_challenges(self):
        calls=[]
        def gen(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(text="それは良かったね。",token_count=6,
                mean_confidence=.8,min_confidence=.5)
        r=evaluate(M(),M(),T(),gen,dataset()["holdout"],EXTRA)
        self.assertEqual(r["holdout_count"],12)
        self.assertEqual(r["challenge_count"],7)
        self.assertEqual(len(r["rows"]),19)
        self.assertEqual(len(calls),38)
        self.assertEqual({c["seed"] for c in calls},{42})
        self.assertEqual({c["temperature"] for c in calls},{0.0})
    def test_human_review_required(self):
        a=assess("それは良かったね。","それは良かったね。","POSITIVE")
        self.assertTrue(a["target_exact"])
        self.assertTrue(a["human_review_required"])
    def test_negative_and_mixed_probes(self):
        names={r["emotion"] for r in EXTRA}
        self.assertIn("MIXED",names)
        self.assertIn("NON_SADNESS",names)
        self.assertIn("IRONY_AMBIGUOUS",names)
    def test_vocabulary_mismatch(self):
        class Bad: vocab_size=10
        with self.assertRaises(ValueError):
            evaluate(Bad(),M(),T(),lambda **kw:None,[],[])
if __name__=="__main__":unittest.main()
