import unittest
from clipboard_context_v0976 import ClipboardContext

MENU="""メニュー
ビバレッジ
ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.
ブラックベリー ヨーグルト フラペチーノ® 白耳 ver.
ビバレッジ一覧へ
フード
ニューヨークチーズケーキ
フード一覧へ
"""
class TasteDialogueTests(unittest.TestCase):
    def setUp(self):
        self.ctx=ClipboardContext()
        self.ctx.set(MENU)
    def start(self):
        return self.ctx.answer("ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.を飲んだことがある")
    def test_two_taste_turns(self):
        self.assertIn("どんな味だった",self.start())
        self.assertIn("飲みやすかった",self.ctx.answer("酸味と甘さのバランスが良かった"))
        self.assertIn("チョコレート",self.ctx.answer("黒耳は、ブラックチョコレートで甘かった"))
    def test_followup_does_not_repeat_catalogue(self):
        self.start()
        self.assertNotIn("白耳 ver.",self.ctx.answer("酸味と甘さのバランスが良かった"))
    def test_unrelated_question_not_intercepted(self):
        self.start()
        self.assertIn("白耳",self.ctx.answer("フラペチーノの種類は"))
    def test_new_clipboard_resets_experience(self):
        self.start()
        self.ctx.set("無関係の文章")
        self.assertIsNone(self.ctx.answer("酸味と甘さのバランスが良かった"))
    def test_taste_reply_without_experience_not_forced(self):
        self.assertIsNone(self.ctx.answer("酸味と甘さのバランスが良かった"))
    def test_two_turn_expiry(self):
        self.start()
        self.ctx.answer("酸味と甘さのバランスが良かった")
        self.ctx.answer("黒耳はブラックチョコレートで甘かった")
        self.assertIsNone(self.ctx.answer("苦味は少なかった"))
if __name__=="__main__": unittest.main()
