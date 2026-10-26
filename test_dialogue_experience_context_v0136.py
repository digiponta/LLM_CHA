import unittest
from unittest.mock import Mock
from dialogue_topic_context_v0135 import TopicContext
from chat_gui_v0119 import ChatGUI

SOURCE=("フード ハーブソーセージ スターバックス バゲットサンド "
        "ハム&ゴーダチーズ スターバックス バゲットサンド "
        "ビバレッジ ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.")

class ExperienceTopicTests(unittest.TestCase):
    def test_food_multi_turn(self):
        ctx=TopicContext()
        self.assertIn("食べてみて",ctx.respond_experience("ハーブソーセージ スターバックス バゲットサンドを食べた",SOURCE))
        self.assertIn("あっさり",ctx.respond_experience("あっさりした味わいで、美味しかった",SOURCE))
        self.assertIn("満足",ctx.respond_experience("満足した",SOURCE))
        self.assertEqual(ctx.state.kind,"experience")
    def test_subject_switch(self):
        ctx=TopicContext()
        ctx.respond_experience("ハーブソーセージ スターバックス バゲットサンドを食べた",SOURCE)
        self.assertIn("それも好き",ctx.respond_experience("ハム&ゴーダチーズ スターバックス バゲットサンドも好き",SOURCE))
        self.assertIn("ハム&ゴーダチーズ",ctx.respond_experience("満足した",SOURCE))
    def test_drink_variant(self):
        ctx=TopicContext()
        self.assertIn("ドリンク",ctx.respond_experience("黒耳を飲んだ",SOURCE))
        self.assertIn("黒耳",ctx.respond_experience("美味しかった",SOURCE))
    def test_no_unverified_knowledge_added(self):
        ctx=TopicContext()
        self.assertIsNone(ctx.respond_experience("未知の商品を食べた",SOURCE))
        self.assertEqual(ctx.state.subject,"")
    def test_reset(self):
        ctx=TopicContext()
        ctx.respond_experience("黒耳を飲んだ",SOURCE)
        ctx.reset()
        self.assertIsNone(ctx.respond_experience("満足した",SOURCE))
    def test_gui_mixed_conversation(self):
        gui=ChatGUI.__new__(ChatGUI)
        gui.entry=Mock(); gui._append=Mock(); gui.submit=Mock()
        gui.clipboard_context=SOURCE; gui.last_clipboard_source=SOURCE
        gui.active_food_item=""; gui.active_preference_topic=""
        gui.topic_context=TopicContext()
        for phrase in ("ハーブソーセージ スターバックス バゲットサンドを食べた",
                       "あっさりした味わいで、美味しかった",
                       "ハム&ゴーダチーズ スターバックス バゲットサンドも好き",
                       "満足した","黒耳を飲んだ","美味しかった"):
            gui.entry.get.return_value=phrase
            gui.send()
        self.assertEqual(gui._append.call_count,6)
        self.assertIn("黒耳",gui._append.call_args.args[0])
        gui.submit.assert_not_called()
if __name__=="__main__":unittest.main()
