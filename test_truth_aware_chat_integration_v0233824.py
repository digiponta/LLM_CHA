"""v0.2.33.82.4 static integration guards + adapter boundary regression.

Actual GPU / Truth Gate output must be validated separately on target hardware.
"""
import pathlib
import unittest
from conversation_topic_adapter_v0233822 import ConversationTopicAdapter

SOURCE = pathlib.Path(__file__).with_name("chat.py")


class TruthAwareChatIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_opt_in_disabled_by_default(self):
        self.assertIn('os.environ.get("LLM_CHA_MULTITOPIC", "0") == "1"', self.source)

    def test_topic_route_precedes_truth_retrieval(self):
        self.assertLess(self.source.index("topic_route = topic_adapter.process_user_turn"),
                        self.source.index("semantic_result = semantic_knowledge.resolve("))

    def test_original_truth_gate_still_present(self):
        self.assertIn("truth_allows_direct_retrieval(", self.source)
        self.assertIn("semantic_knowledge.resolve(", self.source)

    def test_reset_clears_only_transient_topic_context(self):
        segment = self.source.split('if command == "/reset":', 1)[1].split("continue", 1)[0]
        self.assertIn("topic_adapter.context.reset()", segment)
        self.assertIn("history.clear()", segment)
        self.assertNotIn("semantic_knowledge.sync_all", segment)
        self.assertNotIn("truth_store", segment)

    def test_slash_command_bypasses_topic_routing(self):
        self.assertLess(self.source.index('if command == "/sleep":'),
                        self.source.index("topic_route = topic_adapter.process_user_turn"))

    def test_ambiguity_never_reaches_generation(self):
        adapter = ConversationTopicAdapter()
        adapter.process_user_turn("宇宙について教えて")
        adapter.process_user_turn("GPUとは")
        route = adapter.process_user_turn("それについて")
        self.assertEqual(route.action, "CLARIFY")
        self.assertIsNone(route.rewritten_query)

    def test_followup_passes_topic_as_question(self):
        adapter = ConversationTopicAdapter()
        adapter.process_user_turn("宇宙について教えて")
        route = adapter.process_user_turn("もう少し詳しく")
        self.assertEqual(route.action, "READY")
        self.assertIn("宇宙", route.rewritten_query)

    def test_unverified_knowledge_not_authored_by_adapter(self):
        self.assertNotIn("return Route(\"ANSWER\"", pathlib.Path(
            __file__).with_name("conversation_topic_adapter_v0233822.py").read_text(
                encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
