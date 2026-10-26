import unittest
from unittest.mock import Mock
from chat_gui_v0119 import ChatGUI, preference_dialogue_reply

class EllipticalPreferenceTests(unittest.TestCase):
    def test_elliptical_sparkle(self):
        result=preference_dialogue_reply("きらきらしてるところが","スファレライト")
        self.assertIn("輝くところ",result)
        self.assertIn("色合い",result)
    def test_earlier_complete_utterance(self):
        self.assertIn("心地よい",preference_dialogue_reply("きらきらしてるところが心地よい","スファレライト"))
    def test_gui_sequence(self):
        gui=ChatGUI.__new__(ChatGUI)
        gui.entry=Mock();gui._append=Mock();gui.submit=Mock()
        gui.clipboard_context="スファレライト 屈折率と輝き"
        gui.last_clipboard_source=gui.clipboard_context
        gui.active_food_item=""
        gui.active_preference_topic=""
        for msg in ("私は、スファレライトが好きです。","きらきらしてるところが","黄色が好きです"):
            gui.entry.get.return_value=msg
            gui.send()
        self.assertEqual(gui._append.call_count,3)
        gui.submit.assert_not_called()

if __name__=="__main__":unittest.main()
