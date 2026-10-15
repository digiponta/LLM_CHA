import unittest
from persona_auto_wiki_v0556 import candidate,enrich

WIKI={"status":"FOUND","title":"量子コンピュータ","url":"https://ja.wikipedia.org/wiki/test",
      "extract":"量子コンピュータは計算機。"}
def lookup(term,context=None):
    return WIKI
def render(wiki,user,persona="nagato"):
    return {"answer":"Wikipediaによると、量子コンピュータは計算機。どの部分を知りたい？",
            "source":"Wikipedia"}

class AutoWikiTests(unittest.TestCase):
 def test_article_term(self):
    self.assertEqual(candidate("今日は量子コンピュータの記事を読んだ"),"量子コンピュータ")
 def test_known_no_lookup(self):
    self.assertIsNone(candidate("今日はGPUの記事を読んだ"))
 def test_daily_no_lookup(self):
    self.assertIsNone(candidate("今日は散歩した"))
 def test_found(self):
    r=enrich("今日は量子コンピュータの記事を読んだ","nagato",lookup,render)
    self.assertEqual(r["status"],"FOUND")
    self.assertEqual(r["truth_state"],"EXTERNAL_UNVERIFIED")
    self.assertFalse(r["train_ready"])
 def test_cache(self):
    seen=[]
    def counting(term,context=None):
        seen.append(term);return WIKI
    c={}
    for _ in range(2):
        enrich("今日は量子コンピュータの記事を読んだ","nagato",counting,render,cache=c)
    self.assertEqual(len(seen),1)
 def test_not_found(self):
    r=enrich("今日は量子コンピュータの記事を読んだ","nagato",
             lambda *a,**k:{"status":"NOT_FOUND"},render)
    self.assertIsNone(r["answer"])
 def test_failed_network(self):
    def fail(*a,**k):raise OSError("offline")
    self.assertEqual(enrich("今日は量子コンピュータの記事を読んだ","nagato",fail,render)["status"],"LOOKUP_FAILED")
 def test_grounded_refusal(self):
    r=enrich("今日は量子コンピュータの記事を読んだ","nagato",lookup,lambda *a,**k:None)
    self.assertEqual(r["status"],"NO_GROUNDED_RESPONSE")
 def test_no_side_effect_on_casual(self):
    def fail(*a,**k):raise AssertionError("should not lookup")
    self.assertEqual(enrich("今日は散歩した","nagato",fail,render)["status"],"NO_CANDIDATE")
 def test_quoted_term(self):
    self.assertEqual(candidate("「トポロジカル量子計算」を見た"),"トポロジカル量子計算")
if __name__=="__main__":unittest.main()
