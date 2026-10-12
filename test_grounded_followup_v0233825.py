"""v0.2.33.82.5 static regression and topic routing behavior.

GPU / live Truth Gate results must be collected on target machine.
"""
import ast
from pathlib import Path
import unittest

from conversation_topic_adapter_v0233822 import ConversationTopicAdapter


class GroundedFollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        ast.parse(cls.source)
        cls.section = cls.source.split(
            "# v0.2.33.82.5: grounded multi-topic follow-up only.", 1
        )[1].split("# v10.16.1 Conditional Semantic Retrieval.", 1)[0]

    def test_follows_original_truth_gate_policy(self):
        self.assertIn("truth_allows_direct_retrieval(", self.section)

    def test_memory_retrieval_for_topic(self):
        self.assertIn("retrieval_first_resolve_subject(", self.section)
        self.assertIn("followup_subject = topic_route.topic", self.section)

    def test_truth_state_uses_topic(self):
        self.assertIn("effective_truth_record(", self.section)
        self.assertIn("truth_store_path, followup_subject", self.section)

    def test_no_unconstrained_generation_in_followup_branch(self):
        self.assertNotIn("generate_reply(", self.section)
        self.assertIn("continue", self.section)

    def test_no_memory_mutation_in_followup_branch(self):
        for prohibited in ("truthset", "sync_all(", "queue_conditional_candidate(",
                           "promote_batch_candidate(", "train("):
            self.assertNotIn(prohibited, self.section)

    def test_unverified_warning(self):
        self.assertIn('followup_truth.state == "UNVERIFIED"', self.section)
        self.assertIn("truth warning:", self.section)

    def test_missing_or_unsafe_fact_fails_closed(self):
        self.assertIn("grounded-followup=BLOCK", self.section)
        self.assertIn("検証可能な追加情報がありません", self.section)

    def test_topic_switch_and_grounded_followup(self):
        adapter = ConversationTopicAdapter()
        adapter.process_user_turn("宇宙について教えて")
        adapter.process_user_turn("GPUとは")
        adapter.process_user_turn("宇宙の話に戻って")
        route = adapter.process_user_turn("もう少し詳しく")
        self.assertEqual(route.topic, "宇宙")
        self.assertEqual(route.action, "READY")

    def test_reset_leaves_no_followup_subject(self):
        adapter = ConversationTopicAdapter()
        adapter.process_user_turn("宇宙について教えて")
        adapter.process_user_turn("/reset")
        self.assertEqual(adapter.process_user_turn("もう少し詳しく").action,
                         "NO_TOPIC")


if __name__ == "__main__":
    unittest.main()
