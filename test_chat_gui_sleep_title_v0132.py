import unittest
from unittest.mock import Mock
from chat_gui_v0119 import ChatGUI, TITLE_BASE, sleep_pending_from_log

class SleepPendingTitleTests(unittest.TestCase):
    def test_startup(self):
        self.assertEqual(sleep_pending_from_log(
            "[Nagato Semantic Memory: corpus_records=72, subjects=56, internalized=56, pending=0]"),0)
    def test_status(self):
        self.assertEqual(sleep_pending_from_log(
            "[semantic sleep: memory=56, internalized=53, pending=3]"),3)
    def test_completed(self):
        self.assertEqual(sleep_pending_from_log(
            "[semantic sleep completed: memory=56, internalized=56, pending=0]"),0)
    def test_other_pending_not_confused(self):
        self.assertIsNone(sleep_pending_from_log("[knowledge queue lifecycle: pending=20]"))
        self.assertIsNone(sleep_pending_from_log("[internalized verification: pending=7]"))
    def test_split_stdout_and_title_change(self):
        gui=ChatGUI.__new__(ChatGUI)
        gui.root=Mock()
        gui.status_line_buffer=""
        gui._update_sleep_title("[Nagato Semantic Memory: internalized=54, pen")
        gui.root.title.assert_not_called()
        gui._update_sleep_title("ding=2]\n")
        gui.root.title.assert_called_once_with(TITLE_BASE+" | /sleep待ち: 2件")
        gui._update_sleep_title("[semantic sleep completed: pending=0]\n")
        self.assertEqual(gui.root.title.call_args.args[0],TITLE_BASE+" | /sleep待ち: 0件")

if __name__=="__main__":
    unittest.main()
