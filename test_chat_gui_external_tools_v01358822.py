import unittest
from unittest.mock import Mock,patch
from chat_gui import ChatGUI

class ExternalToolsTests(unittest.TestCase):
 def fake(self):
  gui=ChatGUI.__new__(ChatGUI)
  gui.entry=Mock()
  gui.entry.get.return_value="スファレライト"
  gui.diagnostics=object()
  gui.add=Mock()
  gui.tabs=Mock()
  gui.root=Mock()
  return gui
 def test_google_uses_encoded_query(self):
  g=self.fake()
  with patch("chat_gui.webbrowser.open",return_value=True) as opener:
   g.google()
  self.assertIn("%E3%82%B9",opener.call_args[0][0])
 def test_clipboard_is_not_submitted_to_chat(self):
  g=self.fake()
  g.root.clipboard_get.return_value="硫化亜鉛（ZnS）"
  with patch("chat_gui.messagebox.showinfo"):
   g.clipboard_read()
  self.assertEqual(g._clipboard_context,"硫化亜鉛（ZnS）")
  self.assertFalse(hasattr(g,"proc"))
 def test_empty_clipboard(self):
  g=self.fake()
  g.root.clipboard_get.return_value=""
  with patch("chat_gui.messagebox.showinfo"):
   g.clipboard_read()
  self.assertFalse(hasattr(g,"_clipboard_context"))
if __name__=="__main__":unittest.main()
