import unittest
from clipboard_context_v0976 import ClipboardContext
from clipboard_product_resolution_v09720 import resolve,classify

MENU="""メニュー
ビバレッジ
ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.
ブラックベリー ヨーグルト フラペチーノ® 白耳 ver.
ビバレッジ一覧へ
フード
ニューヨークチーズケーキ
フード一覧へ
"""
class ProductResolutionTests(unittest.TestCase):
    def setUp(self):
        self.ctx=ClipboardContext()
        self.ctx.set(MENU)
    def test_short_past_tense(self):
        r=self.ctx.answer("ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.を飲んだ")
        self.assertIn("どんな味だった",r)
        self.assertTrue(self.ctx.dialogue.taste_turns)
    def test_short_alias_experience(self):
        self.assertIn("どんな味だった",self.ctx.answer("黒耳を飲んだ"))
        self.assertIn("黒耳 ver.",self.ctx.dialogue.experience_product)
    def test_taste_without_prior_context(self):
        self.assertIn("味の感想",self.ctx.answer("黒耳は、ブラックチョコレートで甘かった"))
    def test_variants_differ(self):
        self.assertIn("白耳 ver.",resolve(MENU,"白耳を飲んだ")["product"])
    def test_question_does_not_get_captured(self):
        self.assertIsNone(classify(MENU,"フラペチーノの種類は"))
        self.assertIn("白耳",self.ctx.answer("フラペチーノの種類は"))
    def test_no_source_product(self):
        self.assertEqual(resolve(MENU,"未知の新商品を飲んだ")["status"],"NONE")
    def test_full_name_ambiguous(self):
        self.assertEqual(resolve(MENU,"黒耳と白耳を飲んだ")["status"],"AMBIGUOUS")
        self.assertIn("どちらの商品",self.ctx.answer("黒耳と白耳を飲んだ"))
    def test_original_taste_sequence_retained(self):
        self.ctx.answer("黒耳を飲んだ")
        self.assertIn("飲みやすかった",self.ctx.answer("酸味と甘さのバランスが良かった"))
        self.assertIn("チョコレート",self.ctx.answer("黒耳は、ブラックチョコレートで甘かった"))
if __name__=="__main__":unittest.main()
