import unittest
from diagnose_models_v0213 import last_user_only,summarize

class PromptDiagnosticTests(unittest.TestCase):
    def test_strip_history(self):
        prompt="人: 最近、本を読んでいます\nAI: どんな本ですか？\n人: SFです"
        self.assertEqual(last_user_only(prompt),"人: SFです")
    def test_no_history(self):
        self.assertEqual(last_user_only("人: SFです"),"人: SFです")
    def test_truncation_input_format(self):
        self.assertEqual(last_user_only("人: 写真です\nAI: そう\n人: 夜景です"),"人: 夜景です")
if __name__=="__main__":unittest.main()
