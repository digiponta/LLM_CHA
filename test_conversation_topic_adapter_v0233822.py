"""v0.2.33.82.2 adapter regression; does not claim live GPU validation."""
import unittest
from conversation_topic_adapter_v0233822 import ConversationTopicAdapter
from multi_topic_context_v0233821 import MultiTopicContext

class ConversationTopicAdapterTests(unittest.TestCase):
    def test_topic_followup(self):
        a = ConversationTopicAdapter()
        self.assertEqual(a.process_user_turn("宇宙について教えて").topic, "宇宙")
        r = a.process_user_turn("もう少し詳しく")
        self.assertEqual(r.action, "READY")
        self.assertIn("宇宙", r.rewritten_query)

    def test_switch_and_return(self):
        a = ConversationTopicAdapter()
        a.process_user_turn("宇宙について教えて")
        a.process_user_turn("GPUとは")
        self.assertEqual(a.process_user_turn("宇宙の話に戻って").topic, "宇宙")
        self.assertEqual(a.process_user_turn("もう少し詳しく").topic, "宇宙")

    def test_ambiguous_reference_requires_clarification(self):
        a = ConversationTopicAdapter()
        a.process_user_turn("宇宙について教えて")
        a.process_user_turn("GPUとは")
        r = a.process_user_turn("それについて")
        self.assertEqual(r.action, "CLARIFY")
        self.assertIsNone(r.rewritten_query)

    def test_unseen_topic_not_invented(self):
        a = ConversationTopicAdapter()
        a.process_user_turn("GPUとは")
        self.assertEqual(a.process_user_turn("量子力学の話に戻って").action, "NO_TOPIC")

    def test_reset(self):
        a = ConversationTopicAdapter()
        a.process_user_turn("宇宙について教えて")
        self.assertEqual(a.process_user_turn("/reset").action, "RESET")
        self.assertEqual(a.process_user_turn("もう少し詳しく").action, "NO_TOPIC")

    def test_other_commands_bypass(self):
        a = ConversationTopicAdapter()
        a.process_user_turn("宇宙について教えて")
        before = a.context.snapshot()
        self.assertEqual(a.process_user_turn("/sleep").action, "COMMAND")
        self.assertEqual(a.context.snapshot(), before)

    def test_truth_gate_boundary(self):
        a = ConversationTopicAdapter()
        r = a.process_user_turn("宇宙について教えて")
        self.assertEqual(r.action, "READY")
        self.assertFalse(hasattr(r, "answer"))
        self.assertNotIn("truth_state", a.context.snapshot())
        # Runtime must call its existing Truth Gate after READY.

    def test_ttl(self):
        a = ConversationTopicAdapter(MultiTopicContext(ttl_turns=1))
        a.process_user_turn("宇宙について教えて")
        a.process_user_turn("こんにちは")
        self.assertEqual(a.process_user_turn("もう少し詳しく").action, "NO_TOPIC")

    def test_empty_or_arbitrary_input_passes(self):
        a = ConversationTopicAdapter()
        self.assertEqual(a.process_user_turn("こんにちは").rewritten_query, "こんにちは")
        self.assertEqual(a.process_user_turn("").action, "READY")

if __name__ == "__main__":
    unittest.main()
