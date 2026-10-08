import unittest
from conversation_quality_gate_v027 import context_quality_decision,repair_reply

class ConversationGateV027Tests(unittest.TestCase):
    def test_reject_generic_continuation(self):
        self.assertEqual(context_quality_decision("その話、続けて","そうですね。"),(False,"generic reply to context request"))
    def test_reject_without_context_too(self):
        self.assertFalse(context_quality_decision("その話、続けて","お願いしますよ!")[0])
    def test_allow_substantive_continuation(self):
        self.assertTrue(context_quality_decision("その話、続けて","SFでは未来社会や宇宙探査などがよく描かれる。")[0])
    def test_accept_short_ack_non_context(self):
        self.assertTrue(context_quality_decision("こんにちは","そうですね。")[0])
    def test_opt_out(self):
        self.assertTrue(context_quality_decision("その話、続けて","そうですね。",enabled=False)[0])
    def test_clarification(self):
        self.assertIn("どの話",repair_reply("その話、続けて",has_context=False))
        self.assertIn("どの部分",repair_reply("その話、続けて",has_context=True))
if __name__=="__main__":unittest.main()
