import unittest
from clipboard_final_guard_v09747 import inspect_clipboard_answer

class ClipboardFinalGuardTests(unittest.TestCase):
    def test_baguette_sandwich_eaten(self):
        name="ハム&ゴーダチーズ スターバックス バゲットサンド"
        r=inspect_clipboard_answer(name+"を食べた","そう、"+name+"を飲んだのね。どんな味だった？")
        self.assertEqual(r.decision,"REJECT")
        self.assertIn(r.reason, ("explicit-user-action-conflict", "semantic-action-consistency"))
        self.assertIn(name+"を食べたのね",r.selected)
    def test_drink_verbs_preserved(self):
        r=inspect_clipboard_answer("ラテを飲んだ","ラテを飲んだのね。")
        self.assertEqual(r.decision,"REVIEW")
    def test_no_mismatched_item(self):
        r=inspect_clipboard_answer("ケーキを食べた","ラテを飲んだんだね。")
        self.assertEqual(r.decision,"REVIEW")
    def test_food_without_user_action(self):
        r=inspect_clipboard_answer("バゲットサンドについて","バゲットサンドを飲んだのね。")
        self.assertEqual(r.decision,"REJECT")
    def test_not_automatic_training(self):
        r=inspect_clipboard_answer("ケーキを食べた","ケーキを飲んだんだね。")
        self.assertFalse(r.train_ready or r.auto_promote or r.persisted)
    def test_unverified_metadata_unchanged(self):
        r=inspect_clipboard_answer("バゲットサンドを食べた","バゲットサンドを飲んだのね。")
        self.assertEqual(r.route,"CLIPBOARD_CONTEXT_ANSWER")
if __name__=="__main__":unittest.main()
