import unittest
from persona_wiki_topic_followup_v0558 import followup

CURRENT={"status":"FOUND","title":"量子ビット","extract":"量子ビットは基本単位。","url":"https://ja.wikipedia.org/wiki/test"}
NEW={"status":"FOUND","title":"量子重ね合わせ","extract":"量子重ね合わせは物理現象。","url":"https://ja.wikipedia.org/wiki/new"}
def lookup(t,context=None):return NEW
def render(w,u,persona="nagato"):return {"answer":"Wikipediaによると、量子重ね合わせは物理現象。","source":w["url"]}
class TopicFollowupTests(unittest.TestCase):
 def test_new_topic(self):
  r=followup("量子重ね合わせについて教えて",CURRENT,"nagato",lookup,render)
  self.assertEqual(r["status"],"FOUND")
  self.assertEqual(r["route"],"PERSONA_WIKIPEDIA_TOPIC_FOLLOWUP")
  self.assertEqual(r["previous_topic"],"量子ビット")
 def test_unverified(self):
  r=followup("量子重ね合わせについて教えて",CURRENT,"nagato",lookup,render)
  self.assertFalse(r["verified"]);self.assertFalse(r["train_ready"]);self.assertFalse(r["auto_promote"])
 def test_absent_context(self):
  self.assertEqual(followup("量子重ね合わせについて教えて",None,"nagato",lookup,render)["status"],"NO_CONTEXT")
 def test_unrelated(self):
  self.assertEqual(followup("今日は散歩した",CURRENT,"nagato",lookup,render)["status"],"NOT_TOPIC_FOLLOWUP")
 def test_ambiguous(self):
  self.assertEqual(followup("それについて教えて",CURRENT,"nagato",lookup,render)["status"],"AMBIGUOUS_TOPIC")
 def test_same_topic(self):
  self.assertEqual(followup("量子ビットについて教えて",CURRENT,"nagato",lookup,render)["status"],"SAME_TOPIC_DEFER")
 def test_failure(self):
  r=followup("量子重ね合わせについて教えて",CURRENT,"nagato",lambda *a,**k:{"status":"NOT_FOUND"},render)
  self.assertEqual(r["status"],"NOT_FOUND")
 def test_quantum_alias_retry(self):
  calls=[]
  def lookup_alias(term,context=None):
   calls.append(term)
   if term=="量子重ね合わせ":
    return {"status":"AMBIGUOUS","candidates":["重ね合わせ","量子力学"]}
   return {"status":"FOUND","title":"重ね合わせ",
           "extract":"量子力学における重ね合わせは複数状態の線形結合。",
           "url":"https://ja.wikipedia.org/wiki/test"}
  def render_alias(w,u,persona="nagato"):
   return {"answer":"Wikipediaによると、量子力学における重ね合わせは複数状態の線形結合。",
           "source":w["url"]}
  r=followup("量子重ね合わせについて教えて",CURRENT,"nagato",lookup_alias,render_alias)
  self.assertEqual(r["status"],"FOUND")
  self.assertEqual(r["lookup_alias"],"重ね合わせ")
  self.assertEqual(calls,["量子重ね合わせ","重ね合わせ"])
 def test_alias_requires_quantum_source(self):
  def unrelated(term,context=None):
   if term=="量子重ね合わせ":return {"status":"AMBIGUOUS"}
   return {"status":"FOUND","title":"重ね合わせ","extract":"画像の合成手法。",
           "url":"https://ja.wikipedia.org/wiki/test"}
  r=followup("量子重ね合わせについて教えて",CURRENT,"nagato",unrelated,render)
  self.assertEqual(r["status"],"AMBIGUOUS")
 def test_cache(self):
  cache={};hits=[]
  def count(term,context=None):hits.append(term);return NEW
  for _ in range(2):followup("量子重ね合わせについて教えて",CURRENT,"nagato",count,render,cache=cache)
  self.assertEqual(len(hits),1)
if __name__=="__main__":unittest.main()
