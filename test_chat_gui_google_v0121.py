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
    def test_clipboard_context_not_consumed(self):
        gui=self.make_gui()
        gui.entry.get.return_value="フードの種類は"
        gui.clipboard_context="フード ハーブソーセージ バゲットサンド フード一覧へ"
        gui.send()
        self.assertIn("バゲットサンド",gui._append.call_args.args[0])
        self.assertEqual(gui.clipboard_context,"フード ハーブソーセージ バゲットサンド フード一覧へ")
        gui.submit.assert_not_called()
if __name__=="__main__":unittest.main()
