import unittest
from unittest.mock import Mock
from chat_gui_v0119 import ChatGUI,preference_dialogue_reply

class MineralColorPreferenceTests(unittest.TestCase):
    def test_yellow_liked(self):
        self.assertIn("色合い",preference_dialogue_reply("黄色が好きです","スファレライト"))
    def test_no_topic(self):
        self.assertIsNone(preference_dialogue_reply("黄色が好きです",""))
    def test_three_turn_dialogue(self):
        gui=ChatGUI.__new__(ChatGUI)
        gui.entry=Mock()
        gui._append=Mock()
        gui.submit=Mock()
        gui.clipboard_context="スファレライトは光が強く輝く"
        gui.last_clipboard_source=gui.clipboard_context
        gui.active_food_item=""
        gui.active_preference_topic=""
        for message in ("私は、スファレライトが好きです。","きらきらしてるところが心地よい","黄色が好きです"):
            gui.entry.get.return_value=message
            gui.send()
        self.assertEqual(gui._append.call_count,3)
        self.assertIn("色合い",gui._append.call_args.args[0])
        gui.submit.assert_not_called()
if __name__=="__main__":unittest.main()
