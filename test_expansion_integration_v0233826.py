"""v0.2.33.82.6 integration safeguards (static + behavioral)."""
import ast
from pathlib import Path
import unittest
from grounded_expansion_v0233826 import PropositionCursor


class ExpansionIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        ast.parse(cls.source)

    def test_flag_retained(self):
        self.assertIn('os.environ.get("LLM_CHA_MULTITOPIC", "0") == "1"', self.source)

    def test_cursor_created_for_opt_in(self):
        self.assertIn("proposition_cursor = PropositionCursor()", self.source)

    def test_cursor_reset_with_context(self):
        self.assertIn("topic_adapter.context.reset()\n                proposition_cursor.reset()", self.source)

    def test_initial_and_followup_use_same_cursor(self):
        self.assertIn("proposition_cursor.next(\n                            retrieval_focus, retrieval.answer", self.source)
        self.assertIn("proposition_cursor.next(\n                    followup_subject, followup_hit.answer", self.source)

    def test_truth_evaluated_before_initial_pagination(self):
        self.assertLess(self.source.index("direct_retrieval_allowed = truth_allows_direct_retrieval("),
                        self.source.index("grounded-expansion=INITIAL"))

    def test_warning_for_unverified(self):
        self.assertIn("【未検証の記録】", self.source)

    def test_exhaustion_no_generation(self):
        self.assertIn("grounded-expansion=EXHAUSTED", self.source)

    def test_full_sequence(self):
        c = PropositionCursor()
        text = "宇宙は膨張する。 / 宇宙は進化する。"
        self.assertEqual(c.next("宇宙", text)[0], "宇宙は膨張する。")
        self.assertEqual(c.next("宇宙", text)[0], "宇宙は進化する。")
        self.assertIsNone(c.next("宇宙", text)[0])


if __name__ == "__main__":
    unittest.main()
