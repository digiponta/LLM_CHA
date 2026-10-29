import unittest
from temporary_evidence_v01358824 import TemporaryEvidence
from general_evidence_retrieval_v01358827 import retrieve
class GeneralRetrievalTests(unittest.TestCase):
 def test_menu(self):
  e=TemporaryEvidence();e.set_topic("スターバックス")
  e.add("スターバックス\nメニュー：ドリップコーヒー、カフェラテ、サンドイッチ","clipboard")
  r=retrieve(e,"メニューは？")
  self.assertEqual(r["status"],"EXCERPTS")
  self.assertIn("ドリップコーヒー",r["quotes"][0])
 def test_food(self):
  e=TemporaryEvidence();e.set_topic("スターバックス")
  e.add("スターバックス\nフード：サンドイッチ、スコーン、ケーキ","clipboard")
  self.assertIn("スコーン",retrieve(e,"フードの種類は？")["quotes"][0])
 def test_no_evidence(self):
  e=TemporaryEvidence();e.set_topic("スターバックス")
  self.assertEqual(retrieve(e,"メニューは？")["status"],"NO_EVIDENCE")
 def test_no_relevance(self):
  e=TemporaryEvidence();e.set_topic("スターバックス")
  e.add("スターバックス\n所在地は東京です。","clipboard")
  self.assertEqual(retrieve(e,"メニューは？")["status"],"NO_MATCH")
 def test_changed_topic(self):
  e=TemporaryEvidence();e.set_topic("スターバックス")
  e.add("スターバックス\nメニュー：カフェラテ","clipboard")
  e.set_topic("スファレライト")
  self.assertEqual(retrieve(e,"メニューは？")["status"],"NO_EVIDENCE")
 def test_no_invented_menu(self):
  e=TemporaryEvidence();e.set_topic("スターバックス")
  e.add("スターバックス\n商品について説明しています。","clipboard")
  self.assertEqual(retrieve(e,"メニューは？")["status"],"NO_MATCH")
if __name__=="__main__":unittest.main()
