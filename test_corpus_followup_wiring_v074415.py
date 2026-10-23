import ast
import unittest
from pathlib import Path

class CorpusFollowupWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chat=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        cls.gui=Path(__file__).with_name("chat_gui_v07447.py").read_text(encoding="utf-8")
        ast.parse(cls.chat)
        ast.parse(cls.gui)
    def test_runtime_guard(self):
        self.assertIn('LLM_CHA_CORPUS_FOLLOWUP',self.chat)
        self.assertIn('guarded_followup = corpus_followup(raw_user_text, corpus_followup_context)',self.chat)
    def test_trusted_stays_unmodified(self):
        self.assertIn('retrieval.route == "CORPUS_MEMORY"',self.chat)
        self.assertIn('retrieval_truth.state == "UNVERIFIED"',self.chat)
    def test_topic_expiry(self):
        self.assertIn('corpus_followup_context = None',self.chat)
    def test_gui_flag(self):
        self.assertIn('env["LLM_CHA_CORPUS_FOLLOWUP"] = "1"',self.gui)

if __name__=="__main__":
    unittest.main()
