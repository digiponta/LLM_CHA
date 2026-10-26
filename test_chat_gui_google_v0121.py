import unittest
from unittest.mock import Mock, patch
from chat_gui_v0119 import ChatGUI, google_query

class LegacyGUIBehavior(unittest.TestCase):
    def make_gui(self):
        gui=ChatGUI.__new__(ChatGUI)
        gui.entry=Mock()
        gui.entry.get.return_value="スファレライトをぐぐって"
        gui.clipboard_context=""
        gui._append=Mock()
        gui.submit=Mock()
        return gui
    def test_google_phrase(self):
        self.assertEqual(google_query("スファレライトをぐぐって"),"スファレライト")
    def test_non_google_phrase(self):
        self.assertIsNone(google_query("スファレライトの成分は"))
    def test_google_opens_browser_not_model(self):
        gui=self.make_gui()
        with patch("chat_gui_v0119.webbrowser.open") as open_page:
            gui.send()
        open_page.assert_called_once()
        self.assertIn("google.com/search?",open_page.call_args.args[0])
        gui.submit.assert_not_called()
    def test_clipboard_temporary_context_one_turn(self):
        gui=self.make_gui()
        gui.entry.get.return_value="化学組成は"
        gui.clipboard_context="化学組成が硫化亜鉛（ZnS）の鉱物"
        gui.send()
        self.assertEqual(gui.clipboard_context,"")
        self.assertIn("ZnS",gui.submit.call_args.args[0])
        self.assertIn("未検証",gui.submit.call_args.args[0])
        gui.send()
        self.assertEqual(gui.submit.call_count,2)
        self.assertEqual(gui.submit.call_args.args[0],"化学組成は")
if __name__=="__main__":unittest.main()
