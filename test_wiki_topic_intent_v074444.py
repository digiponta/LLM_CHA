import unittest
from wiki_topic_intent_v074444 import is_topic_request
class TopicIntentTests(unittest.TestCase):
    def test_colloquial_request(self):
        for q in ("何か話題はないか","何か話題はある？","話題を提供して","何か面白い話題は？","/topic"):
            with self.subTest(q=q): self.assertTrue(is_topic_request(q))
    def test_regular_question(self):
        for q in ("量子力学とは","もっと詳しく","はい","今日は何曜日"):
            with self.subTest(q=q): self.assertFalse(is_topic_request(q))
    def test_chat_route(self):
        from pathlib import Path
        code=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn("if is_topic_request(user_text):",code)
if __name__=="__main__":unittest.main()
