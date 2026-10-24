import unittest
from pathlib import Path
from wiki_dual_context_v08013 import DualWikiContext

class DualContextTests(unittest.TestCase):
    def setUp(self):
        self.c=DualWikiContext()
        self.c.select("古典ビット","量子ビット")
    def test_separate_subjects(self):
        self.assertEqual(self.c.summary()["requested_topic"],"古典ビット")
        self.assertEqual(self.c.summary()["selected_article"],"量子ビット")
        self.assertEqual(self.c.summary()["relation"],"RELATED_UNVERIFIED")
    def test_original_topic_navigation(self):
        self.assertEqual(self.c.intent("元の話題について教えて")["topic"],"古典ビット")
        self.assertEqual(self.c.intent("古典ビットそのものについて教えて")["target"],"REQUESTED")
    def test_selected_article_navigation(self):
        self.assertEqual(self.c.intent("選んだ記事について詳しく")["topic"],"量子ビット")
    def test_status_and_clear(self):
        self.assertEqual(self.c.intent("今の話題は")["target"],"STATUS")
        self.c.clear()
        self.assertIsNone(self.c.intent("今の話題は"))
    def test_runtime_wired(self):
        code=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn("wiki_dual_context.select(requested_topic,chosen)",code)
        self.assertIn("WIKIPEDIA_DUAL_CONTEXT_STATUS",code)
if __name__=="__main__": unittest.main()
