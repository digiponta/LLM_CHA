import unittest
from audit_vocabulary_calibrated_v013588298 import audit
class M:
 def __init__(self,x):self.x=x
 def surface(self):return self.x
class T:
 def tokenize(self,x):return [M(a) for a in x.split()]
class TestCalibrated(unittest.TestCase):
 def test_exact_phrase_exemption(self):
  x=audit("閃亜鉛鉱 別名",{"別名":2},T(),["閃亜鉛鉱"])
  self.assertEqual(x["status"],"CORPUS_COVERED")
  self.assertEqual(x["exempt_expression_occurrences"],1)
 def test_missing_is_not_proven_invented(self):
  x=audit("あくまで もち",{},T())
  self.assertEqual(x["status"],"OUT_OF_CORPUS_REVIEW")
  self.assertFalse(x["invented_word_confirmed"])
 def test_exemption_not_substring(self):
  x=audit("別名 別名語",{"別名":2},T(),["別名"])
  self.assertEqual(x["out_of_corpus_terms"],["語"])
 def test_no_semantic_claim(self):
  x=audit("猫",{"猫":1},T())
  self.assertFalse(x["semantic_relevance_evaluated"])
if __name__=="__main__":unittest.main()
