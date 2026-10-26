"""Scoped regression for v0.9.7.58 source-first topic handling."""
import unittest

from topic_clipboard_bridge_v09758 import answer_from_topic_clipboard
from topic_keyed_context_v09756 import TopicContext

SOURCE = "スファレライトは化学組成が硫化亜鉛（ZnS）の鉱物である。"


class TopicClipboardBridgeTests(unittest.TestCase):
    def test_explicit_topic(self):
        topic = TopicContext()
        self.assertIsNotNone(topic.observe("スファレライトの成分は"))
        answer = answer_from_topic_clipboard("スファレライトの成分は", topic.active_topic, SOURCE)
        self.assertIn("ZnS", answer)
        self.assertIn("未検証", answer)

    def test_followup(self):
        topic = TopicContext()
        topic.observe("スファレライトの成分は")
        self.assertIsNotNone(topic.observe("化学組成を知りたい"))
        self.assertIn("ZnS", answer_from_topic_clipboard("化学組成を知りたい", topic.active_topic, SOURCE))

    def test_missing_source(self):
        self.assertIsNone(answer_from_topic_clipboard("成分は", "スファレライト", ""))

    def test_wrong_topic(self):
        self.assertIsNone(answer_from_topic_clipboard("化学組成を知りたい", "ダイヤモンド", SOURCE))

    def test_unrelated_question(self):
        self.assertIsNone(answer_from_topic_clipboard("産地を知りたい", "スファレライト", SOURCE))

    def test_no_source_fabrication(self):
        self.assertIsNone(answer_from_topic_clipboard("化学組成を知りたい", "スファレライト", "スファレライトは美しい宝石。"))


if __name__ == "__main__":
    unittest.main()
