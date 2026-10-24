import unittest
from pathlib import Path
from wiki_topic_switch_guard_v0807 import explicit_topic,should_reset_wiki_context

class WikiTopicSwitchTests(unittest.TestCase):
    def test_explicit_topic_switch(self):
        self.assertTrue(should_reset_wiki_context("古典ビットについて教えて",{"title":"量子ビット"}))
    def test_same_topic(self):
        self.assertFalse(should_reset_wiki_context("量子ビットについて教えて",{"title":"量子ビット"}))
    def test_elided_followup(self):
        self.assertFalse(should_reset_wiki_context("もう少し詳しく",{"title":"量子ビット"}))
    def test_missing_context(self):
        self.assertFalse(should_reset_wiki_context("古典ビットについて教えて",None))
    def test_runtime_wired_before_followup(self):
        code=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        start=code.index("if should_reset_wiki_context(raw_user_text,cha_wiki_conversation.current):")
        self.assertLess(start,code.index("topic_followup=cha_wiki_topic_followup(",start))
        self.assertIn("cha_wiki_conversation.clear()",code[start:start+250])

if __name__=="__main__":unittest.main()
