import unittest
from wiki_topic_attribute_v013588213 import resolve_question,search_for_question
def finder(topic):
 hits=[{"title":"閃亜鉛鉱","extract":"閃亜鉛鉱はスファレライトとも呼ばれる。硬度は3.5から4である。","url":"https://ja.wikipedia.org/wiki/閃亜鉛鉱"}]
 return {"status":"HIT","hits":hits}
class WikiTopicTests(unittest.TestCase):
 def test_compound(self):
  self.assertEqual(resolve_question("スファレライトの屈折率は？"),{"topic":"スファレライト","attribute":"屈折率"})
 def test_followup(self):
  self.assertEqual(resolve_question("硬度は？","スファレライト")["topic"],"スファレライト")
 def test_not_answered_by_article_hit(self):
  self.assertEqual(search_for_question("スファレライトの屈折率は？",searcher=finder)["status"],"NO_ATTRIBUTE_EVIDENCE")
 def test_attribute_excerpt(self):
  x=search_for_question("スファレライトの硬度は？",searcher=finder)
  self.assertEqual(x["status"],"HIT")
  self.assertIn("硬度",x["hits"][0]["extract"])
 def test_definition_single_result(self):
  self.assertEqual(len(search_for_question("スファレライトとは？",searcher=finder)["hits"]),1)
 def test_no_hit(self):
  x=search_for_question("未知の用語とは？",searcher=lambda q:{"status":"NO_HIT","hits":[]})
  self.assertEqual(x["status"],"NO_HIT")
if __name__=="__main__":unittest.main()
