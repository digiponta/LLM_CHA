import unittest
from temporary_evidence_v01358824 import TemporaryEvidence
class EvidenceTests(unittest.TestCase):
 def test_grounded(self):
  s=TemporaryEvidence();s.set_topic("スファレライト")
  s.add("化学組成：ZnS（硫化亜鉛）","clipboard")
  self.assertIn("ZnS",s.answer("化学組成は？"))
 def test_no_evidence(self):
  s=TemporaryEvidence();s.set_topic("スファレライト")
  self.assertIsNone(s.answer("化学組成は？"))
 def test_other_question(self):
  s=TemporaryEvidence();s.set_topic("スファレライト")
  s.add("化学組成：ZnS（硫化亜鉛）","clipboard")
  self.assertIsNone(s.answer("価格は？"))
 def test_unrelated_topic(self):
  s=TemporaryEvidence();s.set_topic("スターバックス")
  s.add("化学組成：ZnS（硫化亜鉛）","clipboard")
  self.assertIsNone(s.answer("化学組成は？"))
if __name__=="__main__":unittest.main()
