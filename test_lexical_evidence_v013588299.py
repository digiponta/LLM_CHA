import unittest
from lexical_evidence_v013588299 import classify
class Morpheme:
 def __init__(self,s,oov):self.s=s;self.oov=oov
 def surface(self):return self.s
 def is_oov(self):return self.oov
class Tokenizer:
 def tokenize(self,s):
  return [Morpheme(x,x.startswith("謎")) for x in s.split()]
class Tests(unittest.TestCase):
 def test_known_dictionary_word_even_if_absent_from_corpus(self):
  result=classify("別名",Tokenizer(),{})
  self.assertEqual(result["items"][0]["category"],"KNOWN_WORD")
 def test_corpus_only(self):
  result=classify("謎単語",Tokenizer(),{"謎単語":3})
  self.assertEqual(result["items"][0]["category"],"CORPUS_ONLY")
 def test_unknown_composition(self):
  result=classify("謎造語",Tokenizer(),{})
  self.assertEqual(result["status"],"REVIEW_REQUIRED")
  self.assertEqual(result["items"][0]["category"],"UNKNOWN_COMPOSITION")
 def test_exempt_before_tokenization(self):
  result=classify("閃亜鉛鉱",Tokenizer(),{},["閃亜鉛鉱"])
  self.assertEqual(result["items"][0]["category"],"SPECIALIZED_TERM")
 def test_no_semantic_claim(self):
  result=classify("世界点",Tokenizer(),{"世界点":2})
  self.assertFalse(result["meaning_verified"])
  self.assertFalse(result["compound_usage_verified"])
if __name__=="__main__":unittest.main()
