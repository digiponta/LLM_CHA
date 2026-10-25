import unittest
from clipboard_context_v0976 import ClipboardContext
from google_browser_search_v0973 import search_intent
MENU="""メニュー
ビバレッジ
パンプキン スパイス ラテ
ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.
ブラックベリー ヨーグルト フラペチーノ® 白耳 ver.
ビバレッジ一覧へ
フード
チーズケーキ
フード一覧へ
"""
class DialogueIntentTests(unittest.TestCase):
    def setUp(self):
        self.c=ClipboardContext()
        self.c.set(MENU)
    def test_menu_then_short_drink(self):
        self.assertIn("どちらを知りたい",self.c.answer("スターバックスのメニューは"))
        self.assertIn("パンプキン スパイス ラテ",self.c.answer("ドリンク"))
    def test_menu_then_short_food(self):
        self.c.answer("スターバックスのメニューは")
        self.assertIn("チーズケーキ",self.c.answer("フード"))
    def test_experience_not_listing(self):
        result=self.c.answer("ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.は、飲んだことがある")
        self.assertIn("どんな味だった",result)
        self.assertNotIn("白耳",result)
    def test_explicit_frappuccino_question_retained(self):
        self.assertIn("白耳",self.c.answer("フラペチーノの種類は"))
    def test_short_without_context_not_forced(self):
        self.assertIsNone(self.c.answer("ドリンク"))
    def test_reset_does_not_reuse_category(self):
        self.c.answer("スターバックスのメニューは")
        self.c.set("無関係の文書")
        self.assertIsNone(self.c.answer("ドリンク"))
    def test_search_spelling_variations(self):
        for value in ("スターバックスをググって","スターバックスをぐぐって","スターバックスをグぐって"):
            self.assertEqual(search_intent(value),"スターバックス")
if __name__=="__main__":unittest.main()
