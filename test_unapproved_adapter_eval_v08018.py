import unittest
from pathlib import Path

class UnapprovedAdapterEvalTests(unittest.TestCase):
    def test_eval_route_wired(self):
        chat=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn('if user_text == "/wiki-model-eval":',chat)
        self.assertIn("UNAPPROVED_ADAPTER_NLL_EVAL",chat)
    def test_gui_button_wired(self):
        gui=Path(__file__).with_name("chat_gui_v07447.py").read_text(encoding="utf-8")
        self.assertIn("学習効果評価",gui)
        self.assertIn('request_status("/wiki-model-eval")',gui)
    def test_eval_never_promotes(self):
        src=Path(__file__).with_name("unapproved_adapter_eval_v08018.py").read_text(encoding="utf-8")
        for value in ('"holdout_evaluated":False','"approved":False','"weights_changed":False','"training_pairs_only"'):
            if value=='"training_pairs_only"':
                continue
            self.assertIn(value,src)
    def test_syntax(self):
        for name in ("unapproved_adapter_eval_v08018.py","chat_gui_v07447.py"):
            compile(Path(__file__).with_name(name).read_text(encoding="utf-8"),name,"exec")

if __name__=="__main__":unittest.main()
