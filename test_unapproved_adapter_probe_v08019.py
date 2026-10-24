import unittest
from pathlib import Path

class ProbeTests(unittest.TestCase):
    def test_syntax(self):
        for filename in ("unapproved_adapter_probe_v08019.py","chat_gui_v07447.py","chat.py"):
            compile(Path(__file__).with_name(filename).read_text(encoding="utf-8"),filename,"exec")
    def test_command_wiring(self):
        chat=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        gui=Path(__file__).with_name("chat_gui_v07447.py").read_text(encoding="utf-8")
        self.assertIn('if user_text == "/wiki-model-probe":',chat)
        self.assertIn('request_status("/wiki-model-probe")',gui)
    def test_no_false_holdout_claims(self):
        source=Path(__file__).with_name("unapproved_adapter_probe_v08019.py").read_text(encoding="utf-8")
        self.assertIn('"independent_holdout":False',source)
        self.assertIn('"unknown_rejection_measured":False',source)
        self.assertIn('"weights_changed":False',source)
if __name__=="__main__":unittest.main()
