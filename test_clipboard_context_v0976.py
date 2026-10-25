import unittest
from clipboard_context_v0976 import ClipboardContext

SAMPLE="""スターバックス コーヒー ジャパン
メニュー
ビバレッジ
パンプキン スパイス ラテ
パンプキン スパイス ラテ
キャラメル マキアート
ビバレッジ一覧へ
フード
手しぼり栗のモンブラン
フード一覧へ
"""
class ClipboardContextTests(unittest.TestCase):
    def test_empty_context_no_routing(self):
        self.assertIsNone(ClipboardContext().answer("メニューは"))
    def test_menu_follows_clipboard(self):
        c=ClipboardContext();c.set(SAMPLE)
        answer=c.answer("メニューは")
        self.assertIn("パンプキン スパイス ラテ",answer)
        self.assertIn("キャラメル マキアート",answer)
        self.assertNotIn("Wikipedia",answer)
    def test_summary(self):
        c=ClipboardContext();c.set(SAMPLE)
        self.assertIn("スターバックス",c.answer("このページを要約して"))
    def test_unrelated_question_falls_through(self):
        c=ClipboardContext();c.set(SAMPLE)
        self.assertIsNone(c.answer("量子力学とは"))
    def test_clear(self):
        c=ClipboardContext();c.set(SAMPLE);c.clear()
        self.assertIsNone(c.answer("メニューは"))
if __name__=="__main__":unittest.main()
