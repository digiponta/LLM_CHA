import unittest
from unittest.mock import Mock, patch
from chat_gui_v0119 import ChatGUI

class ClipboardTests(unittest.TestCase):
    def test_clipboard_load_to_input_without_sending(self):
        gui=ChatGUI.__new__(ChatGUI)
        gui.root=Mock()
        gui.root.clipboard_get.return_value="資料1\n資料2"
        gui.entry=Mock()
        gui._append=Mock()
        gui.process=None
        gui.read_clipboard()
        gui.entry.insert.assert_called_once_with(0,"資料1 資料2")
        gui._append.assert_called_once()
    def test_empty_clipboard_warns(self):
        gui=ChatGUI.__new__(ChatGUI)
        gui.root=Mock()
        gui.root.clipboard_get.return_value=""
        gui.entry=Mock()
        gui._append=Mock()
        with patch("chat_gui_v0119.messagebox.showwarning") as warning:
            gui.read_clipboard()
            warning.assert_called_once()
        gui.entry.insert.assert_not_called()
if __name__=="__main__":unittest.main()
