import unittest
from japanese_repair_gate_v09745 import repair_and_recheck,fluency_diagnostic

class JapaneseRepairTests(unittest.TestCase):
    def test_fluency_flag(self):
        self.assertEqual(fluency_diagnostic("疲れたんだね。良かったんでしたね。")[0],"FAIL")
    def test_reviewed_repair(self):
        r=repair_and_recheck("楽しかったけど疲れた","疲れたんだね。良かったんでしたね。")
        self.assertEqual(r.decision,"REPAIRED")
        self.assertEqual(r.selected_response,"お疲れ様でした。楽しかったようで良かったですね。")
        self.assertEqual(r.second_gate,"ACCEPT")
    def test_polarity_fallback(self):
        r=repair_and_recheck("今日は楽しかった","悲しかったんだね。")
        self.assertEqual(r.decision,"FALLBACK")
        self.assertIn("良かった",r.selected_response)
    def test_ambiguous_abstains(self):
        r=repair_and_recheck("量子力学について教えて","あの")
        self.assertEqual(r.decision,"ABSTAIN")
    def test_unknown_fluent_also_abstains(self):
        r=repair_and_recheck("量子力学について教えて","量子力学では波動関数を使います。")
        self.assertEqual(r.decision,"ABSTAIN")
        self.assertEqual(r.first_gate,"ABSTAIN")
    def test_no_automatic_promotion(self):
        r=repair_and_recheck("楽しかったけど疲れた","疲れたんだね。良かったんでしたね。")
        self.assertFalse(r.train_ready or r.auto_promote or r.persisted)
    def test_good_reply_requires_review(self):
        r=repair_and_recheck("今日は楽しかった","楽しい一日だったんだね。")
        self.assertEqual(r.decision,"REVIEW")
if __name__=="__main__":unittest.main()
