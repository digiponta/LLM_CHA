"""Regression checks for GUI input modes and exit controls."""
import unittest
from pathlib import Path
from chat_window_v061 import build_chat_command

class GuiExitTests(unittest.TestCase):
    def test_gui_only_switch_is_not_forwarded_to_chat(self):
        command,_=build_chat_command(["--gui-only-input","--final-guard"])
        self.assertIn("--final-guard",command)
        self.assertNotIn("--gui-only-input",command)

    def test_exit_button_and_bounded_shutdown_are_present(self):
        source=Path(__file__).with_name("chat_window_v061.py").read_text(encoding="utf-8")
        self.assertIn('text="/exit", command=trigger_exit',source)
        self.assertIn('send_to_chat("/exit", show_user=False)',source)
        self.assertIn("child.wait(timeout=3)",source)
        self.assertIn("child.terminate()",source)

if __name__=="__main__":
    unittest.main()
