import unittest
from pathlib import Path
from wiki_topic_switch_guard_v0807 import explicit_topic,should_reset_wiki_context
from unknown_wiki_fallback_v0557 import fallback

class IndependentTopicTests(unittest.TestCase):
    def test_switch(self):
        self.assertTrue(should_reset_wiki_context("古典ビットについて教えて",{"title":"量子ビット"}))
        self.assertEqual(explicit_topic("古典ビットについて教えて"),"古典ビット")
    def test_mismatch_rejected(self):
        def lookup(term,context=None):
            return {"status":"FOUND","title":"量子ビット","url":"https://example.org","extract":"量子情報"}
        def render(wiki,question,persona="nagato"):
            return {"answer":"wrong article"}
        result=fallback("古典ビット","古典ビットについて教えて","nagato",lookup,render)
        self.assertEqual(result["status"],"TOPIC_MISMATCH")
    def test_runtime_independent_lookup(self):
        code=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn("EXPLICIT_TOPIC_INDEPENDENT_WIKIPEDIA",code)
        self.assertIn("prior_context_reused=False",code)
if __name__=="__main__": unittest.main()
