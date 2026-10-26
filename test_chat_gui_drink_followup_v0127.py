import unittest
from unittest.mock import Mock
from chat_gui_v0119 import ChatGUI, clipboard_answer, contextual_followup, selected_item_from_utterance

SOURCE=("ビバレッジ ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver. "
"ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver. "
"スターバックス ラテ スターバックス ラテ ビバレッジ一覧へ "
"フード ハーブソーセージ スターバックス バゲットサンド フード一覧へ")

class DrinkRegressions(unittest.TestCase):
    def test_drink_list_present(self):
        a=clipboard_answer(SOURCE,"ドリンクの種類は")
        self.assertIn("黒耳",a)
        self.assertIn("スターバックス ラテ",a)
        self.assertNotIn("一覧は確認できません",a)
    def test_black_ear_drank(self):
        a=contextual_followup(SOURCE,"黒耳を飲んだ")
        self.assertIsNotNone(a)
        self.assertIn("飲ん",a)
        self.assertEqual(selected_item_from_utterance(SOURCE,"黒耳を飲んだ"),"黒耳")
    def test_gui_black_ear_while_clipboard_persists(self):
        gui=ChatGUI.__new__(ChatGUI)
        gui.entry=Mock()
        gui._append=Mock()
        gui.submit=Mock()
        gui.clipboard_context=SOURCE
        gui.last_clipboard_source=SOURCE
        gui.active_food_item=""
        for question in ("ドリンクの種類は","黒耳を飲んだ"):
            gui.entry.get.return_value=question
            gui.send()
        self.assertIn("飲ん",gui._append.call_args.args[0])
        self.assertEqual(gui.active_food_item,"黒耳")
        gui.submit.assert_not_called()
if __name__=="__main__":unittest.main()
