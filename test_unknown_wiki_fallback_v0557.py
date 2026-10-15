import unittest
from unknown_wiki_fallback_v0557 import fallback
W={"status":"FOUND","title":"量子ビット","url":"https://ja.wikipedia.org/wiki/test","extract":"量子ビットは量子情報の単位。"}
def lookup(t,context=None):return W
def render(w,u,persona="nagato"):return {"answer":"Wikipediaによると、量子ビットは量子情報の単位。","source":w["url"]}
class UnknownWikiTests(unittest.TestCase):
 def test_unknown_definition(self):
  x=fallback("量子ビット","量子ビットとは？","nagato",lookup,render)
  self.assertEqual(x["status"],"FOUND");self.assertEqual(x["route"],"UNKNOWN_WIKIPEDIA_FALLBACK")
 def test_unverified(self):
  x=fallback("量子ビット","量子ビットとは？","nagato",lookup,render)
  self.assertFalse(x["verified"]);self.assertFalse(x["train_ready"]);self.assertFalse(x["auto_promote"])
 def test_cache(self):
  hits=[]
  def count(t,context=None):hits.append(t);return W
  cache={}
  for _ in range(2):fallback("量子ビット","量子ビットとは？","nagato",count,render,cache=cache)
  self.assertEqual(hits,["量子ビット"])
 def test_not_found(self):
  x=fallback("量子ビット","量子ビットとは？","nagato",lambda *a,**k:{"status":"NOT_FOUND"},render)
  self.assertEqual(x["status"],"NOT_FOUND")
 def test_failure(self):
  def fail(*a,**k):raise OSError("offline")
  self.assertEqual(fallback("量子ビット","量子ビットとは？","nagato",fail,render)["status"],"LOOKUP_FAILED")
 def test_empty_concept(self):self.assertEqual(fallback("","質問","nagato",lookup,render)["status"],"INVALID_CONCEPT")
 def test_no_grounded_answer(self):
  self.assertEqual(fallback("量子ビット","質問","nagato",lookup,lambda *a,**k:None)["status"],"NO_GROUNDED_ANSWER")
 def test_grounded_fallback(self):
  x=fallback("量子ビット","質問","nagato",lookup,lambda *a,**k:None,grounded=lambda w,u:{"answer":"Wikipedia抜粋","source":"Wikipedia"})
  self.assertEqual(x["status"],"FOUND")
if __name__=="__main__":unittest.main()
