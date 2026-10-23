import ast
import unittest
from pathlib import Path
from unittest.mock import patch
from topic_recovery_v074413 import resolve

class TopicNormalizationRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chat = Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        cls.gui = Path(__file__).with_name("chat_gui_v07447.py").read_text(encoding="utf-8")
        ast.parse(cls.chat)
        ast.parse(cls.gui)
    def test_normalization_target(self):
        result = resolve("量子重ね合わせについて教えて")
        self.assertEqual(result.topic, "重ね合わせ")
    def test_explicit_wikipedia_lookup(self):
        self.assertIn("normalized_wiki = cha_unknown_wiki_fallback(", self.chat)
        self.assertIn("route=TOPIC_ALIAS_WIKIPEDIA",self.chat)
    def test_preserves_input(self):
        anchor=self.chat.index("# v0.7.44.14:")
        block=self.chat[anchor:self.chat.index("relation = relation_context.observe",anchor)]
        self.assertNotIn("user_text = cha_topic_plan.query", block)
        self.assertIn("truth_allows_direct_retrieval",block)
        self.assertIn("train_ready=False, auto_promote=False",block)
    def test_gui_enabled(self):
        self.assertIn('env["LLM_CHA_TOPIC_NORMALIZE"] = "1"',self.gui)
    def test_followup_unintegrated(self):
        # No premature promise of evidence-aware continuation.
        self.assertNotIn("FOLLOWUP_EVIDENCE",self.chat)

if __name__=="__main__":
    unittest.main()
