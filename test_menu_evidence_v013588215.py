import unittest
from menu_evidence_v013588215 import retrieve_menu, format_menu

class Store:
    topic = "スターバックス"
    records = [{"topic": "スターバックス", "source": "clipboard", "text":
        "スターバックス メニュー\nドリンク\n"
        "ブラックベリー ヨーグルト フラペチーノ 黒耳 ver.\n"
        "ブラックベリー ヨーグルト フラペチーノ 白耳 ver.\n"
        "フード\nハーブソーセージ バゲットサンド\n"
        "チョコレートチャンクスコーン\nチョコレートチャンクスコーン"}]

class Tests(unittest.TestCase):
    def test_menu(self):
        x = retrieve_menu(Store(), "メニューは")
        self.assertEqual(x["categories"], ["ドリンク", "フード"])
    def test_drink_list(self):
        x = retrieve_menu(Store(), "ドリンクの種類は")
        self.assertEqual(len(x["items"]["ドリンク"]), 2)
    def test_food_dedup(self):
        x = retrieve_menu(Store(), "フードの種類は")
        self.assertEqual(len(x["items"]["フード"]), 2)
        self.assertIn("バゲットサンド", format_menu(x))
    def test_no_evidence(self):
        class Empty:
            topic = "スターバックス"
            records = []
        self.assertEqual(retrieve_menu(Empty(), "メニューは")["status"], "NO_EVIDENCE")
    def test_no_guess(self):
        class Bare:
            topic = "スターバックス"
            records = [{"topic": "スターバックス", "source": "clipboard", "text": "スターバックス メニュー"}]
        self.assertEqual(retrieve_menu(Bare(), "フードの種類")["status"], "NO_MATCH")
    def test_scope(self):
        s = Store()
        s.records = Store.records + [{"topic": "別の店", "source": "clipboard", "text": "コーヒーラテ"}]
        self.assertEqual(len(retrieve_menu(s, "ドリンクの種類")["items"]["ドリンク"]), 2)

if __name__ == "__main__":
    unittest.main()
