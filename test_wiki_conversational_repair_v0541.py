import ast
import unittest
from pathlib import Path
from wiki_conversational_repair_v0541 import render
E={"status":"EVIDENCE_FOUND","topic":"量子コンピュータ","evidence_span":"量子コンピュータは量子力学の原理を計算に応用したコンピュータである","source":"https://ja.wikipedia.org/wiki/量子コンピュータ","verified":False,"train_ready":False,"promoted":False}
class ConversationalRepairTests(unittest.TestCase):
 def test_article(self):
  r=render("今日は、量子コンピュータの記事を読んだ",E)
  self.assertIn("どんな内容が紹介されていた？",r["answer"])
  self.assertEqual(r["response_intent"],"ARTICLE_SHARING")
 def test_evidence_exact(self):
  r=render("今日は、量子コンピュータの記事を読んだ",E)
  self.assertIn(E["evidence_span"],r["answer"])
  self.assertTrue(r["evidence_preserved"])
 def test_explicit(self):
  r=render("今日は量子コンピュータの記事を読んだ",E,explicit=True)
  self.assertEqual(r["response_intent"],"TOPIC_LOOKUP")
 def test_other(self):
  r=render("量子コンピュータとは",E)
  self.assertEqual(r["response_intent"],"TOPIC_LOOKUP")
 def test_not_found(self):
  result={"status":"NOT_FOUND","answer":"なし"}
  self.assertIs(render("話題",result),result)
 def test_no_promotion(self):
  r=render("今日は量子コンピュータの記事を読んだ",E)
  self.assertFalse(r["verified"]);self.assertFalse(r["train_ready"]);self.assertFalse(r["promoted"])
 def test_source(self):
  self.assertEqual(render("記事",E)["source"],E["source"])
 def test_chat(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(s)
  self.assertIn("cha_wiki_conversational_render",s)
if __name__=="__main__":unittest.main()
