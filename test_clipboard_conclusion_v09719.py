import unittest
from clipboard_context_v0976 import ClipboardContext

MENU="""メニュー
ビバレッジ
ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.
ブラックベリー ヨーグルト フラペチーノ® 白耳 ver.
ビバレッジ一覧へ
フード
チーズケーキ
フード一覧へ
"""
class ConclusionTests(unittest.TestCase):
    def setUp(self):
        self.ctx=ClipboardContext()
        self.ctx.set(MENU)
    def discuss(self):
        self.ctx.answer("ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.を飲んだことがある")
        self.ctx.answer("酸味と甘さのバランスが良かった")
        self.ctx.answer("黒耳は、ブラックチョコレートで甘かった")
    def test_conclusion_single_turn(self):
        self.discuss()
        self.assertTrue(self.ctx.dialogue.awaiting_conclusion)
        self.assertIsNone(self.ctx.dialogue.experience_product)
        self.assertIn("満足できた",self.ctx.answer("満足"))
        self.assertFalse(self.ctx.dialogue.awaiting_conclusion)
    def test_satisfied_variant(self):
        self.discuss()
        self.assertIn("満足できた",self.ctx.answer("満足した"))
    def test_standalone_word_not_intercepted(self):
        self.assertIsNone(self.ctx.answer("満足"))
    def test_unrelated_switch_expires(self):
        self.discuss()
        self.assertIn("白耳",self.ctx.answer("フラペチーノの種類は"))
        self.assertFalse(self.ctx.dialogue.awaiting_conclusion)
        self.assertIsNone(self.ctx.answer("満足した"))
    def test_reload_expires(self):
        self.discuss()
        self.ctx.set(MENU)
        self.assertFalse(self.ctx.dialogue.awaiting_conclusion)
    def test_no_product_retention(self):
        self.discuss()
        self.assertIsNone(self.ctx.dialogue.experience_product)
        self.assertEqual(self.ctx.dialogue.taste_turns,0)
if __name__=="__main__":unittest.main()
