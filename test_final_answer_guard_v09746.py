import unittest
from final_answer_guard_v09746 import daily_intent,inspect_answer

class FinalAnswerGuardTests(unittest.TestCase):
    def test_satisfaction_daily(self):
        result=daily_intent("満足した")
        self.assertEqual(result.route,"DAILY_SATISFACTION")
        self.assertIn("満足",result.selected)
    def test_satisfaction_word_is_not_daily(self):
        self.assertIsNone(daily_intent("満足という言葉の意味は？"))
    def test_broken_nagato_output(self):
        result=inspect_answer("こんにちは","長門有希丘陵、瀬料水産基地)。")
        self.assertEqual(result.decision,"REJECT")
        self.assertFalse(result.train_ready)
    def test_food_drink_conflict(self):
        result=inspect_answer("バゲットサンドを食べた","バゲットサンドを飲んだのね。")
        self.assertEqual(result.decision,"REJECT")
        self.assertIn("食べた",result.selected)
    def test_drink_not_replaced(self):
        result=inspect_answer("ラテを飲んだ","ラテを飲んだんだね。")
        self.assertEqual(result.decision,"REVIEW")
    def test_suspect_not_claimed_correct(self):
        result=inspect_answer("今日は楽しかった","楽しかったんだね。")
        self.assertEqual(result.decision,"REVIEW")
    def test_flags(self):
        result=daily_intent("満足した")
        self.assertFalse(result.train_ready or result.auto_promote or result.persisted)
if __name__=="__main__":unittest.main()
