import unittest
from unittest.mock import Mock
from chat_gui_v0119 import ChatGUI,clipboard_answer,contextual_followup
SOURCE=("ビバレッジ スターバックス ラテ スターバックス ラテ "
        "キャラメル マキアート キャラメル マキアート ビバレッジ一覧へ "
        "フード ハム&ゴーダチーズ スターバックス バゲットサンド "
        "フード一覧へ")
class TopicSwitchTests(unittest.TestCase):
    def test_also_like(self):
        a=contextual_followup(SOURCE,"ハム&ゴーダチーズ スターバックス バゲットサンドも好き")
        self.assertIsNotNone(a)
        self.assertIn("好き",a)
    def test_drinks(self):
        a=clipboard_answer(SOURCE,"ドリンクの種類は")
        self.assertIn("スターバックス ラテ",a)
    def test_multiturn_topic_switch(self):
        gui=ChatGUI.__new__(ChatGUI)
        gui.entry=Mock()
        gui._append=Mock()
        gui.submit=Mock()
        gui.clipboard_context=SOURCE
        gui.last_clipboard_source=SOURCE
        gui.active_food_item=""
        for msg in ("ハム&ゴーダチーズ スターバックス バゲットサンドも好き","ドリンクの種類は"):
            gui.entry.get.return_value=msg
            gui.send()
        self.assertEqual(gui._append.call_count,2)
        self.assertIn("ラテ",gui._append.call_args.args[0])
        self.assertEqual(gui.active_food_item,"ハム&ゴーダチーズ スターバックス バゲットサンド")
        gui.submit.assert_not_called()
if __name__=="__main__":unittest.main()
