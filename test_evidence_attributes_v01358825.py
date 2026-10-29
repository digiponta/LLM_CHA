import unittest
from temporary_evidence_v01358824 import TemporaryEvidence
SAMPLE="""スファレライト
基本データ
化学組成：ZnS（硫化亜鉛）
モース硬度：3.5 〜 4（低く脆い）
屈折率：2.37（ダイヤモンドは2.42）
産地：スペイン、ブルガリア、メキシコ、アメリカ、カナダなど。
"""
class AttributeEvidenceTests(unittest.TestCase):
 def setUp(self):
  self.store=TemporaryEvidence();self.store.set_topic("スファレライト")
  self.store.add(SAMPLE,"clipboard")
 def test_composition(self):self.assertIn("ZnS",self.store.answer("化学組成は？"))
 def test_origin(self):self.assertIn("スペイン",self.store.answer("産地は？"))
 def test_refractive_index(self):self.assertIn("2.37",self.store.answer("屈折率は？"))
 def test_hardness(self):self.assertIn("3.5",self.store.answer("硬度は？"))
 def test_unknown_attr(self):self.assertIsNone(self.store.answer("価格は？"))
 def test_missing_value(self):
  e=TemporaryEvidence();e.set_topic("スファレライト");e.add("スファレライトについての説明","clipboard")
  self.assertIsNone(e.answer("産地は？"))
 def test_unrelated_document(self):
  e=TemporaryEvidence();e.set_topic("スファレライト");e.add("別の石\n屈折率：1.5","clipboard")
  self.assertIsNone(e.answer("屈折率は？"))
 def test_no_cross_topic(self):
  self.store.set_topic("CPU")
  self.assertIsNone(self.store.answer("屈折率は？"))
if __name__=="__main__":unittest.main()
