import unittest
from menu_evidence_v013588215 import retrieve_menu, format_menu

class Store:
    topic="スターバックス"
    records=[{"topic":"スターバックス","source":"clipboard","text":"""
スターバックス コーヒー ジャパン
ドリンク
クリア コーヒー
シトラス クリア コーヒー
ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.
キャラメル マキアート
ビバレッジ一覧へ
コーヒー豆
ティー・紅茶
フード
パンプキン スパイス ラテ
パンプキン スープチーノ®
抹茶あんバター チョコスコーンサンド
手しぼり栗のモンブラン
青森県産2種のりんご カスタードアップルパイ
ハーブソーセージ スターバックス バゲットサンド
ニューヨークチーズケーキ
フード一覧へ
カテゴリー
季節のおすすめ
Seasonal Offering
Beans
Tealeaf
タンブラー＆マグカップ
Tumbler & Mug
Goods
Brewing
GIFT at STARBUCKS
Company
会社案内
採用TOP
Our Mission,
Promises and Values
Social Impact
People & Community
Planet
よくあるご質問・お問い合わせ
サイトマップ
instagram
facebook
© 2026 Starbucks Coffee Company. All rights reserved.
"""}]
class FilteringTests(unittest.TestCase):
    def test_foods_only(self):
        x=retrieve_menu(Store(),"フードの種類は")
        names=x["items"]["フード"]
        self.assertEqual(len(names),6)
        self.assertIn("青森県産2種のりんご カスタードアップルパイ",names)
        self.assertNotIn("Company",names)
        self.assertNotIn("カテゴリー",names)
        self.assertNotIn("パンプキン スパイス ラテ",names)
    def test_drink_excludes_nav(self):
        x=retrieve_menu(Store(),"ドリンクの種類は")
        names=x["items"]["ドリンク"]
        self.assertIn("キャラメル マキアート",names)
        self.assertNotIn("ビバレッジ一覧へ",names)
        self.assertNotIn("コーヒー豆",names)
        self.assertNotIn("コーヒー器具",names)
    def test_menu_sections(self):
        self.assertEqual(retrieve_menu(Store(),"メニューは")["categories"],["ドリンク","フード"])

if __name__=="__main__":
    unittest.main()
