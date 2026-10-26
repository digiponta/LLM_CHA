import unittest
from chat_gui_v0119 import contextual_followup
class ContextFollowupTests(unittest.TestCase):
    def test_ate_item_in_clipboard(self):
        text="フード ハーブソーセージ スターバックス バゲットサンド フード一覧へ"
        r=contextual_followup(text,"ハーブソーセージ スターバックス バゲットサンドを食べた")
        self.assertIn("どうでしたか",r)
    def test_unknown_item_not_intercepted(self):
        self.assertIsNone(contextual_followup("メニュー: ラテ","別の商品を食べた"))
    def test_general_question_not_intercepted(self):
        self.assertIsNone(contextual_followup("バゲットサンド","フードの種類は"))
if __name__=="__main__": unittest.main()
