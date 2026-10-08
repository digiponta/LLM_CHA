import unittest
from conversation_context_v025 import ConversationContext

class ContextTests(unittest.TestCase):
    def test_rejected_user_turn_survives(self):
        c=ConversationContext()
        c.add_user("最近、小説にはまっています")
        c.mark_answered()
        c.add_user("SFです") # generated reply rejected
        c.add_user("その話、続けて")
        self.assertEqual(c.pending_prefix(current="その話、続けて"),"SFです。その話、続けて")
    def test_accepted_turn_not_repeated(self):
        c=ConversationContext()
        c.add_user("SFです");c.mark_answered()
        c.add_user("その話、続けて")
        self.assertEqual(c.pending_prefix(current="その話、続けて"),"その話、続けて")
    def test_reset(self):
        c=ConversationContext()
        c.add_user("SFです");c.clear();c.add_user("その話、続けて")
        self.assertEqual(c.pending_prefix(current="その話、続けて"),"その話、続けて")
    def test_factual_turn_not_promoted_to_chatter(self):
        c=ConversationContext()
        c.add_user("CPUとは");c.add_user("次の話")
        self.assertEqual(c.pending_prefix(current="次の話"),"次の話")
    def test_never_use_rejected_ai_text(self):
        c=ConversationContext()
        c.add_user("SFです")
        c.add_user("続けて")
        self.assertNotIn("未学習です",c.pending_prefix(current="続けて"))
if __name__=="__main__": unittest.main()
