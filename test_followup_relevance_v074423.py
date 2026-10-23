import ast
import unittest
from pathlib import Path

class FollowupRelevanceWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chat=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        cls.gui=Path(__file__).with_name("chat_gui_v07447.py").read_text(encoding="utf-8")
        ast.parse(cls.chat)
        ast.parse(cls.gui)
    def test_fallback_precedes_identity(self):
        start=self.chat.index('FOLLOWUP_RELEVANCE_NO_EVIDENCE')
        identity=self.chat.index('identity_result = identity_context.respond(user_text)')
        self.assertLess(start,identity)
    def test_topic_requires_explicit_subject(self):
        self.assertIn('last_explicit_knowledge_topic = raw_user_text.split("とは", 1)[0].strip()',self.chat)
    def test_guard_opt_in(self):
        self.assertIn('env["LLM_CHA_FOLLOWUP_RELEVANCE"] = "1"',self.gui)
    def test_no_learning(self):
        self.assertIn('route=FOLLOWUP_RELEVANCE_NO_EVIDENCE, topic={}, train_ready=False, auto_promote=False',self.chat)

if __name__=="__main__":
    unittest.main()
