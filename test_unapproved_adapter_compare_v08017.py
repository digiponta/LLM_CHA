import unittest
from pathlib import Path
from unapproved_adapter_compare_v08017 import compare,greedy

class AdapterComparisonTests(unittest.TestCase):
    def test_invalid_question_rejected_without_loading(self):
        self.assertEqual(compare("  ","missing.pt","missing.json","missing.pt")["status"],"INVALID_QUESTION")
    def test_invalid_limit_rejected(self):
        with self.assertRaises(ValueError):
            compare("量子ビットとは","missing.pt","missing.json","missing.pt",max_new_tokens=0)
    def test_runtime_and_gui_wired(self):
        chat=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        gui=Path(__file__).with_name("chat_gui_v07447.py").read_text(encoding="utf-8")
        self.assertIn("/wiki-model-compare ",chat)
        self.assertIn("WIKI_UNAPPROVED_MODEL_COMPARE",chat)
        self.assertIn("未承認LLM比較",gui)
    def test_model_isolation_explicit(self):
        code=Path(__file__).with_name("unapproved_adapter_compare_v08017.py").read_text(encoding="utf-8")
        self.assertIn("base hash mismatch",code)
        self.assertIn('load_state_dict(ck["adapter"],strict=True)',code)
        self.assertIn('"generation_verified":False',code)

if __name__=="__main__":unittest.main()
