import unittest
from conversation_context_v025 import ConversationContext
from conversation_gate_v0219 import rescue_casual_gate,topic_followup

def check(**changes):
    d=dict(user_text="最近、SF小説を読んでいます",answer="そう。どんな本を読んでいるの?",
           intent="general",semantic_ok=True,slot_coverage=1.0,
           confidence=0.584,min_token_conf=0.071,mean_margin=0.520,
           semantic_agreement=0.934,
           rejection_reason="semantic-only rescue with very low lexical agreement")
    d.update(changes)
    return rescue_casual_gate(**d)

class ConversationGateTests(unittest.TestCase):
    def test_rescue_sf_chatter(self):
        self.assertTrue(check())
    def test_knowledge_remains_blocked(self):
        self.assertFalse(check(user_text="長門有希について教えて"))
        self.assertFalse(check(user_text="CPUとは"))
        self.assertFalse(check(truth_restricted=True))
    def test_low_quality_does_not_pass(self):
        self.assertFalse(check(answer="未学習です"))
        self.assertFalse(check(min_token_conf=0.01))
        self.assertFalse(check(semantic_agreement=0.6))
        self.assertFalse(check(repeat=True))
        self.assertFalse(check(context_ok=False))
        self.assertFalse(check(rejection_reason="unfulfilled context request"))
    def test_followup_uses_only_user_context(self):
        c=ConversationContext()
        c.add_user("最近、SF小説を読んでいます")
        c.add_user("その話を続けて")
        self.assertEqual(topic_followup("その話を続けて",c),
                         "最近、SF小説を読んでいます。その話を続けて")
    def test_followup_without_context(self):
        c=ConversationContext()
        c.add_user("その話を続けて")
        self.assertEqual(topic_followup("その話を続けて",c),"その話を続けて")
if __name__=="__main__":unittest.main()
