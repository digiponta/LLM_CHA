import unittest
from chat_gui_v0119 import should_display_line, clipboard_answer

class CleanGUIOutputTests(unittest.TestCase):
    def test_hide_diagnostics(self):
        self.assertFalse(should_display_line("[normalized input: 'text' -> 'normalized']"))
        self.assertFalse(should_display_line("[gate=UNKNOWN, confidence=0.2]"))
        self.assertFalse(should_display_line("[60 generated probe tokens, 0.72s, 83 tok/s]"))
    def test_show_answer(self):
        self.assertTrue(should_display_line("AI> こんにちは"))
    def test_clipboard_food_grounding(self):
        source="スターバックス フード 抹茶あんバター チョコスコーンサンド 手しぼり栗のモンブラン フード一覧へ"
        a=clipboard_answer(source,"フードの種類は")
        self.assertIn("モンブラン",a)
        self.assertIn("未検証",a)
if __name__=="__main__":unittest.main()
