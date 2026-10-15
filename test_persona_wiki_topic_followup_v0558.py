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
 def test_cache(self):
  cache={};hits=[]
  def count(term,context=None):hits.append(term);return NEW
  for _ in range(2):followup("量子重ね合わせについて教えて",CURRENT,"nagato",count,render,cache=cache)
  self.assertEqual(len(hits),1)
if __name__=="__main__":unittest.main()
