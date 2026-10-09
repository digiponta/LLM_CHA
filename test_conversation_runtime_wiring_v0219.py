import unittest
from pathlib import Path
from conversation_context_v025 import ConversationContext
from conversation_gate_v0219 import topic_followup

class RuntimeWiringTests(unittest.TestCase):
    def test_runtime_defaults_enable_dialogue_without_character(self):
        code=Path("chat.py").read_text(encoding="utf-8")
        self.assertIn('parser.add_argument("--dialogue-history-turns", type=int, default=2',code)
        start=code.index("        from_chatter = (")
        end=code.index("        if from_chatter:",start)
        self.assertNotIn("active_character is not None",code[start:end])
        self.assertIn("topic_followup(user_text, conversation_context)",code)
    def test_context_after_rejected_turn(self):
        context=ConversationContext()
        context.add_user("最近、SF小説を読んでいます")
        context.add_user("その話を続けて")
        candidate=context.pending_prefix(current="その話を続けて")
        self.assertIn("SF小説",candidate)
if __name__=="__main__":unittest.main()
