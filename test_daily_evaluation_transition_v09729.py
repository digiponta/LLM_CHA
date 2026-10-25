import unittest
from clipboard_context_v0976 import ClipboardContext
from daily_evaluation_intent_v09729 import classify_evaluation

MENU="""メニュー
ビバレッジ
ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.
ビバレッジ一覧へ
フード
ケーキ
フード一覧へ
"""

class EarlyConclusionTests(unittest.TestCase):
    def setUp(self):
        self.ctx=ClipboardContext()
        self.ctx.set(MENU)
    def begin(self):
        self.ctx.answer("黒耳を飲んだ")
    def test_immediate_satisfaction(self):
        self.begin()
        self.assertEqual(self.ctx.answer("満足した"),"それは良かったね。")
        s=self.ctx.semantic.snapshot()
        self.assertEqual(s["status"],"CLOSED")
        self.assertEqual(s["evaluation"]["emotion"],"POSITIVE")
    def test_disappointment(self):
        self.begin()
        self.assertEqual(self.ctx.answer("期待外れだった"),"それは残念だったね。")
        self.assertEqual(self.ctx.semantic.snapshot()["evaluation"]["emotion"],"DISAPPOINTMENT")
    def test_sadness(self):
        self.begin()
        self.assertEqual(self.ctx.answer("悲しかった"),"それは悲しかったね。")
    def test_one_taste_then_conclusion(self):
        self.begin()
        self.ctx.answer("酸味と甘さのバランスが良かった")
        self.assertEqual(self.ctx.answer("満足した"),"それは良かったね。")
        self.assertIn("acidity",self.ctx.semantic.snapshot()["attributes"])
    def test_two_tastes_then_conclusion(self):
        self.begin()
        self.ctx.answer("酸味と甘さのバランスが良かった")
        self.ctx.answer("黒耳は、ブラックチョコレートで甘かった")
        self.assertIn("満足できた",self.ctx.answer("満足した"))
    def test_no_product_context(self):
        self.assertNotEqual(self.ctx.answer("満足した"),"それは良かったね。")
    def test_unrelated_clears_context(self):
        self.begin()
        self.ctx.answer("フードの種類は")
        self.assertNotEqual(self.ctx.answer("満足した"),"それは良かったね。")
    def test_questions_not_captured(self):
        self.begin()
        self.assertIsNone(classify_evaluation("満足した？"))
if __name__=="__main__":unittest.main()
