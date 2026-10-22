import unittest
from topic_evidence_gate_v0618 import topic_for_external_evidence, source_is_usable

class TopicEvidenceTests(unittest.TestCase):
    def test_starbucks(self):
        self.assertEqual(topic_for_external_evidence("スターバックスの話題"),"スターバックス")
    def test_starbuck_ambiguous(self):
        self.assertEqual(topic_for_external_evidence("スターバックの話題"),"スターバック")
    def test_conversation_protected(self):
        self.assertIsNone(topic_for_external_evidence("長門"))
        self.assertIsNone(topic_for_external_evidence("こんにちは"))
    def test_wiki_source_required(self):
        self.assertFalse(source_is_usable({"status":"FOUND","answer":"根拠がない文を返すだけです"}))
    def test_wiki_answer_required(self):
        self.assertFalse(source_is_usable({"status":"FOUND","source":"https://example.com","answer":"短い"}))
    def test_grounded_response(self):
        self.assertTrue(source_is_usable({"status":"FOUND","source":"https://ja.wikipedia.org/wiki/Starbucks","answer":"スターバックスはコーヒーチェーンです。"}))
if __name__=="__main__":unittest.main()
