import unittest
from gui_semantic_preview_v09745 import semantic_preview,format_preview

class GuiSemanticPreviewTests(unittest.TestCase):
    def test_joy_reversal_shows_candidate(self):
        x=semantic_preview("今日は楽しかった","悲しかったんだね。")
        self.assertEqual(x["decision"],"FALLBACK")
        self.assertIn("良かった",x["suggestion"])
        self.assertIn("未送信",format_preview(x))
    def test_reviewed_repair(self):
        x=semantic_preview("楽しかったけど疲れた","疲れたんだね。良かったんでしたね。")
        self.assertEqual(x["decision"],"REPAIRED")
        self.assertIn("お疲れ様でした",x["suggestion"])
    def test_irrelevant_question_untouched(self):
        self.assertIsNone(semantic_preview("量子力学について教えて","量子力学について説明します。"))
    def test_does_not_promote(self):
        x=semantic_preview("悲しくない","悲しいんだね。")
        self.assertTrue(x["read_only"])
        self.assertFalse(x["approved_for_training"])
    def test_unknown_has_no_forced_preview(self):
        self.assertIsNone(semantic_preview("/status","結果"))
if __name__=="__main__":unittest.main()
