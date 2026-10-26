import unittest
from unittest.mock import Mock
from dialogue_topic_context_v0135 import TopicContext
from chat_gui_v0119 import ChatGUI

class TopicContextRegression(unittest.TestCase):
    def test_sphalerite_full_dialogue(self):
        ctx=TopicContext()
        messages=[
            "私は、スファレライトが好きです。",
            "きらきらしてるところが心地よい",
            "黄色が好きです",
            "そうだよ",
        ]
        answers=[ctx.respond(x) for x in messages]
        self.assertTrue(all(answers))
        self.assertIn("スファレライト",answers[0])
        self.assertIn("色合い",answers[1])
        self.assertIn("色合い",answers[2])
        self.assertEqual(ctx.state.subject,"スファレライト")
    def test_elliptical_answer(self):
        ctx=TopicContext()
        ctx.respond("私は、スファレライトが好きです。")
        self.assertIn("色合い",ctx.respond("きらきらしてるところが"))
    def test_unknown_question_unhandled(self):
        ctx=TopicContext()
        ctx.respond("私は、スファレライトが好きです。")
        self.assertIsNone(ctx.respond("屈折率は？"))
    def test_reset_on_new_clipboard(self):
        ctx=TopicContext()
        ctx.respond("私は、スファレライトが好きです。")
        ctx.reset()
        self.assertIsNone(ctx.respond("黄色が好きです"))
    def test_gui_route_with_real_topic_context(self):
        gui=ChatGUI.__new__(ChatGUI)
        gui.entry=Mock();gui._append=Mock();gui.submit=Mock()
        gui.clipboard_context="スファレライトの屈折率は高い。"
        gui.last_clipboard_source=gui.clipboard_context
        gui.active_preference_topic=""
        gui.active_food_item=""
        gui.topic_context=TopicContext()
        for message in ("私は、スファレライトが好きです。","きらきらしてるところが心地よい","黄色が好きです"):
            gui.entry.get.return_value=message
            gui.send()
        self.assertEqual(gui._append.call_count,3)
        self.assertIn("色合い",gui._append.call_args.args[0])
        gui.submit.assert_not_called()

if __name__=="__main__":unittest.main()
