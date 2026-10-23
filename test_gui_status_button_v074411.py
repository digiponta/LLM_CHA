import ast
import unittest
from pathlib import Path

class StatusButtonWiringTests(unittest.TestCase):
    def test_gui_uses_implemented_command(self):
        source=Path(__file__).with_name("chat_gui_v07447.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn('send("/semstatus", False)',source)
        self.assertNotIn('send("/status",False)',source)
        self.assertIn('events.put(("command_output", captured))',source)
        self.assertIn('tk.Toplevel(root)',source)

if __name__=="__main__":
    unittest.main()
