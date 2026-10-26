import unittest
from unittest.mock import Mock
from chat_gui_v0119 import ChatGUI, preference_dialogue_reply

SOURCE="スファレライトは屈折率が高く、劈開がありカットが難しい。"
class PreferenceDialogueTests(unittest.TestCase):
    def test_sparkle_reaction(self):
        result=preference_dialogue_reply("きらきらしてるところが心地よい","スファレライト")
        self.assertIn("きらきら",result)
        self.assertIn("スファレライト",result)
    def test_acknowledgement(self):
        self.assertIn("スファレライト",preference_dialogue_reply("そうだよ","スファレライト"))
    def test_no_unrelated_topic(self):
        self.assertIsNone(preference_dialogue_reply("そうだよ",""))
    def test_full_gui_dialogue(self):
        gui=ChatGUI.__new__(ChatGUI)
        gui.entry=Mock()
        gui._append=Mock()
        gui.submit=Mock()
        gui.clipboard_context=SOURCE
        gui.last_clipboard_source=SOURCE
        gui.active_food_item=""
        gui.active_preference_topic=""
        for question in ("私は、スファレライトが好きです。","きらきらしてるところが心地よい","そうだよ"):
            gui.entry.get.return_value=question
            gui.send()
        self.assertEqual(gui.active_preference_topic,"スファレライト")
        self.assertEqual(gui._append.call_count,3)
        self.assertIn("魅力",gui._append.call_args.args[0])
        gui.submit.assert_not_called()
if __name__=="__main__":unittest.main()
