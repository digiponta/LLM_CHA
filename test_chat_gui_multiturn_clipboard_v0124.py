import unittest
from unittest.mock import Mock
from chat_gui_v0119 import ChatGUI, clipboard_answer

SOURCE=("スターバックス メニュー ビバレッジ ラテ フード "
        "抹茶あんバター チョコスコーンサンド "
        "ハーブソーセージ スターバックス バゲットサンド "
        "フード一覧へ カテゴリー コーヒー豆 ティー・紅茶")

class MultiTurnClipboardRegression(unittest.TestCase):
    def test_both_questions_supported_by_same_source(self):
        menu=clipboard_answer(SOURCE,"メニューは")
        food=clipboard_answer(SOURCE,"フードの種類は")
        self.assertIn("ビバレッジ",menu)
        self.assertIn("フード",menu)
        self.assertIn("ハーブソーセージ",food)
    def test_gui_two_questions_no_model_submission(self):
        gui=ChatGUI.__new__(ChatGUI)
        gui.entry=Mock()
        gui._append=Mock()
        gui.submit=Mock()
        gui.clipboard_context=SOURCE
        gui.last_clipboard_source=SOURCE
        for question in ("メニューは","フードの種類は"):
            gui.entry.get.return_value=question
            gui.send()
        self.assertEqual(gui._append.call_count,2)
        self.assertIn("バゲットサンド",gui._append.call_args.args[0])
        gui.submit.assert_not_called()
        self.assertEqual(gui.last_clipboard_source,SOURCE)
if __name__=="__main__":unittest.main()
