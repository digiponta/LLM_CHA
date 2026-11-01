import unittest
from build_vocabulary_index_v013588297 import build
from vocabulary_grounded_decoder_v013588297 import audit
class Morph:
 def __init__(self,s):self.s=s
 def surface(self):return self.s
class Tokenizer:
 def tokenize(self,s):return [Morph(x) for x in s.split()]
class VocabularyGuardTest(unittest.TestCase):
 def test_build_counts(self):
  result=build([{"user":"こんにちは 猫","assistant":"猫 です"},{"user":"猫","assistant":"こんにちは"}],Tokenizer(),2)
  self.assertEqual(result["counts"]["猫"],3)
  self.assertEqual(result["counts"]["こんにちは"],2)
  self.assertNotIn("です",result["counts"])
 def test_unknown_review(self):
  out=audit("猫 謎造語",{"猫":3},Tokenizer())
  self.assertEqual(out["status"],"REVIEW")
  self.assertEqual(out["unknown_terms"],["謎造語"])
 def test_domain_override(self):
  out=audit("猫 スファレライト",{"猫":3},Tokenizer(),["スファレライト"])
  self.assertEqual(out["status"],"IN_VOCABULARY")
 def test_no_semantic_claim(self):
  out=audit("猫",{"猫":3},Tokenizer())
  self.assertIsNone(out["candidate_is_semantically_relevant"])
if __name__=="__main__":unittest.main()
