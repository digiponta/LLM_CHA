import ast
import unittest
from pathlib import Path

class RuntimeExhaustionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        ast.parse(cls.source)
    def test_state_exists(self):
        self.assertIn("followup_exhaustion = FollowupExhaustion()",self.source)
    def test_repeated_reply(self):
        self.assertIn("followup_exhaustion.respond(last_explicit_knowledge_topic)",self.source)
    def test_reset_on_topic_change(self):
        self.assertGreaterEqual(self.source.count("followup_exhaustion.reset()"),2)
    def test_no_training(self):
        self.assertIn("route=FOLLOWUP_RELEVANCE_NO_EVIDENCE, topic={}, train_ready=False, auto_promote=False",self.source)

if __name__=="__main__":
    unittest.main()
