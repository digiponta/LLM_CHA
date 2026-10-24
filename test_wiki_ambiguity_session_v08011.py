import unittest
from pathlib import Path
from wiki_ambiguity_session_v08011 import PendingWikiTopic

class AmbiguousWikiSessionTests(unittest.TestCase):
    def setUp(self):
        self.s=PendingWikiTopic()
        self.s.start("古典ビット",{"status":"AMBIGUOUS","candidates":["ビット","量子ビット"]})
    def test_prompt_candidates(self):
        self.assertIn("古典ビット",self.s.message())
        self.assertIn("1:ビット",self.s.message())
    def test_selection(self):
        self.assertEqual(self.s.selection("1")["title"],"ビット")
    def test_followup_does_not_hallucinate(self):
        self.assertEqual(self.s.selection("もう少し詳しく")["status"],"PENDING")
    def test_cancel(self):
        self.assertEqual(self.s.selection("キャンセル")["status"],"CANCELLED")
        self.assertIsNone(self.s.topic)
    def test_unrelated_new_question_clears(self):
        self.assertIsNone(self.s.selection("別の質問"))
        self.assertIsNone(self.s.topic)
    def test_runtime_wired(self):
        content=Path(__file__).with_name("chat.py").read_text(encoding="utf-8")
        self.assertIn("WIKIPEDIA_AMBIGUITY_PENDING",content)
        self.assertIn("WIKIPEDIA_AMBIGUITY_USER_SELECTED",content)
if __name__=="__main__":unittest.main()
