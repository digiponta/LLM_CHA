import unittest
from clipboard_context_v0976 import ClipboardContext
from clipboard_grounded_qa_v0977 import section_items,answer_from_clipboard

TEXT="""スターバックス コーヒー ジャパン
メニュー
ビバレッジ
パンプキン スパイス ラテ
パンプキン スパイス ラテ
ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.
ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.
キャラメル マキアート
ビバレッジ一覧へ
フード
手しぼり栗のモンブラン
手しぼり栗のモンブラン
ニューヨークチーズケーキ
フード一覧へ
"""
class GroundedQATests(unittest.TestCase):
    def test_food_items(self):
        result=answer_from_clipboard(TEXT,"フードには何がある？")
        self.assertIn("手しぼり栗のモンブラン",result["answer"])
        self.assertNotIn("パンプキン スパイス ラテ",result["answer"])
    def test_frappuccino_items(self):
        result=answer_from_clipboard(TEXT,"フラペチーノの種類は？")
        self.assertIn("ブラックベリー",result["answer"])
        self.assertNotIn("キャラメル マキアート",result["answer"])
    def test_beverages(self):
        self.assertIn("キャラメル マキアート",answer_from_clipboard(TEXT,"飲み物は何がある？")["answer"])
    def test_deduplicated(self):
        self.assertEqual(section_items(TEXT)["フード"].count("手しぼり栗のモンブラン"),1)
    def test_recommendation_not_fabricated(self):
        result=answer_from_clipboard(TEXT,"おすすめは？")
        self.assertEqual(result["evidence"],[])
        self.assertIn("判断できません",result["answer"])
    def test_clipboard_context_routes(self):
        context=ClipboardContext();context.set(TEXT)
        self.assertIn("ニューヨークチーズケーキ",context.answer("フードには何がある？"))
    def test_unrelated_falls_through(self):
        self.assertIsNone(answer_from_clipboard(TEXT,"量子力学とは"))
    def test_original_menu_still_supported(self):
        context=ClipboardContext();context.set(TEXT)
        self.assertIn("メニュー",context.answer("メニューは"))
if __name__=="__main__":unittest.main()
