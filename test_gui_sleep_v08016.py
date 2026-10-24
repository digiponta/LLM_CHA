import unittest
from pathlib import Path
from gui_sleep_summary_v08016 import summarize_sleep_output

class GuiSleepSummaryTests(unittest.TestCase):
    def test_trained(self):
        result=summarize_sleep_output("[unapproved wiki sleep: status=TRAINED, eligible=2, trained=True, checkpoint=results/a.pt, trusted_changed=False, approved=False]")
        self.assertEqual(result["state"],"TRAINED")
        self.assertIn("対象2件",result["label"])
    def test_repeated(self):
        result=summarize_sleep_output("[unapproved wiki sleep: status=ALREADY_TRAINED, eligible=2, trained=False, checkpoint=results/a.pt]")
        self.assertEqual(result["state"],"ALREADY_TRAINED")
    def test_failed(self):
        self.assertEqual(summarize_sleep_output("[unapproved wiki sleep FAILED: ValueError: invalid]")["state"],"FAILED")
    def test_skipped(self):
        self.assertEqual(summarize_sleep_output("[experimental sleep FAILED: ValueError: bad]")["state"],"SKIPPED")
    def test_gui_wiring(self):
        source=Path(__file__).with_name("chat_gui_v07447.py").read_text(encoding="utf-8")
        self.assertIn('request_status("/sleep")',source)
        self.assertIn('summarize_sleep_output(value)',source)
        self.assertIn('pending_status["command"] != "/sleep"',source)

if __name__=="__main__":unittest.main()
