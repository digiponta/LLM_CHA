import unittest
from product_dialogue_v013588217 import ProductDialogue
from menu_evidence_v013588215 import extract_menu

TEXT = """ドリンク
ブラックベリー ヨーグルト フラペチーノ® 黒耳 ver.
パンプキン スパイス ラテ
パンプキン スープチーノ®
フード
ハム&ゴーダチーズ スターバックス バゲットサンド
ニューヨークチーズケーキ
フード一覧へ
Company
採用TOP
"""
RECORDS=[{"topic":"スターバックス","text":TEXT,"source":"clipboard"}]
class Tests(unittest.TestCase):
 def test_preference(self):
  p=ProductDialogue()
  ans=p.respond("ハム&ゴーダチーズ スターバックス バゲットサンドも好き",RECORDS,"スターバックス")
  self.assertIn("どんなところ",ans)
 def test_short_alias(self):
  p=ProductDialogue()
  ans=p.respond("黒耳を飲んだ",RECORDS,"スターバックス")
  self.assertIn("フラペチーノ",ans)
 def test_impression_followup(self):
  p=ProductDialogue()
  p.respond("黒耳を飲んだ",RECORDS,"スターバックス")
  self.assertIn("気に入っている",p.respond("甘みの味がいい",RECORDS,"スターバックス"))
 def test_unknown_product_not_invented(self):
  self.assertIsNone(ProductDialogue().respond("不明な製品も好き",RECORDS,"スターバックス"))
 def test_drink_priority(self):
  _,products=extract_menu(RECORDS,"スターバックス")
  self.assertIn("パンプキン スパイス ラテ",products["ドリンク"])
  self.assertNotIn("パンプキン スパイス ラテ",products["フード"])
 def test_footer_excluded(self):
  _,products=extract_menu(RECORDS,"スターバックス")
  self.assertNotIn("Company",products["フード"])
if __name__=="__main__":unittest.main()
