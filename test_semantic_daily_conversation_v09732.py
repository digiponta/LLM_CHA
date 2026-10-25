import unittest
from daily_conversation_foundation_v09728 import dataset as previous
from semantic_daily_conversation_v09732 import build,audit

class SemanticDailyTests(unittest.TestCase):
    def test_original_holdout_preserved_and_untrained(self):
        d=build()
        old={r["input"] for r in previous()["holdout"]}
        self.assertTrue(old.issubset({r["input"] for r in d["holdout"]}))
        self.assertTrue(old.isdisjoint({r["input"] for r in d["train"]}))
        self.assertFalse(d["holdout_used_for_training"])
    def test_labels(self):
        d=build()
        labels={r["semantic"]["emotion"] for r in d["train"]}
        self.assertTrue({"MIXED","NEGATED_POSITIVE","NEGATED_SADNESS"}.issubset(labels))
    def test_no_exact_train_holdout_leakage(self):
        d=build()
        self.assertFalse(set(r["input"] for r in d["train"]) &
                         set(r["input"] for r in d["holdout"]))
        self.assertFalse(audit()["train_holdout_overlap"])
    def test_contrastive_pair(self):
        train={r["input"]:r["target"] for r in build()["train"]}
        self.assertIn("残念",train["今日は楽しくなかった"])
        self.assertNotIn("残念",train["今日は悲しくなかった"])
if __name__=="__main__":unittest.main()
