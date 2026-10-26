import unittest
from unittest.mock import Mock
from chat_gui_v0119 import ChatGUI, reply_to_experience

SOURCE="メニュー ハーブソーセージ スターバックス バゲットサンド フード一覧へ"

class FoodConversationTests(unittest.TestCase):
    def test_taste_response(self):
        self.assertIn("あっさり",reply_to_experience("あっさりした味わいで、美味しかった","ハーブソーセージ スターバックス バゲットサンド"))
    def test_satisfaction_response(self):
        self.assertIn("満足",reply_to_experience("満足した","ハーブソーセージ スターバックス バゲットサンド"))
    def test_without_topic_no_assumption(self):
        self.assertIsNone(reply_to_experience("満足した",""))
    def test_dialogue_remembers_food(self):
        gui=ChatGUI.__new__(ChatGUI)
        gui.entry=Mock()
        gui._append=Mock()
        gui.submit=Mock()
        gui.clipboard_context=SOURCE
        gui.last_clipboard_source=SOURCE
        gui.active_food_item=""
        for msg in ("ハーブソーセージ スターバックス バゲットサンドを食べた",
                    "あっさりした味わいで、美味しかった","満足した"):
            gui.entry.get.return_value=msg
            gui.send()
        self.assertEqual(gui.active_food_item,"ハーブソーセージ スターバックス バゲットサンド")
        self.assertEqual(gui._append.call_count,3)
        self.assertIn("満足",gui._append.call_args.args[0])
        gui.submit.assert_not_called()

if __name__=="__main__":unittest.main()
