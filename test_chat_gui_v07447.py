"""Model-free tests for standalone GUI process configuration."""
import unittest
from unittest.mock import patch
from chat_gui_v07447 import create_process

class GuiLaunchTests(unittest.TestCase):
    @patch("chat_gui_v07447.subprocess.Popen")
    def test_quality_gate_enabled(self, popen):
        create_process(["python","chat.py"], True)
        self.assertEqual(popen.call_args.kwargs["env"]["LLM_CHA_RESPONSE_GATE"],"1")
    @patch("chat_gui_v07447.subprocess.Popen")
    def test_quality_gate_disabled(self, popen):
        create_process(["python","chat.py"], False)
        self.assertEqual(popen.call_args.kwargs["env"]["LLM_CHA_RESPONSE_GATE"],"0")
    @patch("chat_gui_v07447.subprocess.Popen")
    def test_utf8_and_pipe(self, popen):
        create_process(["python","chat.py"])
        self.assertEqual(popen.call_args.kwargs["encoding"],"utf-8")
        self.assertIsNotNone(popen.call_args.kwargs["stdin"])

if __name__=="__main__":
    unittest.main()
