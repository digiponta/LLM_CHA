import ast
import unittest
from pathlib import Path

class GuiStatusV074412Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path(__file__).with_name("chat_gui_v07447.py").read_text(encoding="utf-8")
        ast.parse(cls.source)
    def test_semantic_status_command(self):
        self.assertIn('request_status("/semstatus")',self.source)
    def test_sleep_status_command(self):
        self.assertIn('request_status("/sleep status")',self.source)
    def test_no_simultaneous_capture(self):
        self.assertIn('if pending_status["command"] is not None:',self.source)
    def test_timeouts_not_silent(self):
        self.assertIn('time.monotonic() - pending_status["started"] > 20',self.source)
    def test_status_output_dialog(self):
        self.assertIn('dialog.title("LLM_CHA " + command)',self.source)

if __name__=="__main__":
    unittest.main()
