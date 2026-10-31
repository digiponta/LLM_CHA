import unittest
from compare_daily_holdout_v013588289 import compare

DATA={"cases":[{"id":"daily-001","question":"今日は何をしてる？"},{"id":"daily-002","question":"今何してる？"}]}
def obs(*rows):return {"runs":list(rows)}
def row(i,answer,human=None):return {"id":i,"display":answer,"candidate":answer,"route":"ACCEPT","human_appropriate":human}
class HoldoutCompareTests(unittest.TestCase):
    def test_missing_is_incomplete(self):
        x=compare(DATA,obs(row("daily-001","はい")),obs(row("daily-001","はい")))
        self.assertEqual(x["status"],"INCOMPLETE")
        self.assertEqual(x["two"]["observed"],1)
        self.assertFalse(x["human_naturalness_verified"])
    def test_complete_unrated_requires_review(self):
        both=obs(row("daily-001","はい"),row("daily-002","そう"))
        x=compare(DATA,both,both)
        self.assertEqual(x["status"],"READY_FOR_HUMAN_REVIEW")
    def test_explicit_human_ratings(self):
        both=obs(row("daily-001","はい",True),row("daily-002","そう",False))
        x=compare(DATA,both,both)
        self.assertEqual(x["status"],"COMPLETE")
        self.assertTrue(x["human_naturalness_verified"])
        self.assertFalse(x["semantic_independence_verified"])
if __name__=="__main__":unittest.main()
