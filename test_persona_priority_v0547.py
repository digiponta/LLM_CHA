import ast
import unittest
from pathlib import Path
from persona_priority_v0547 import apply,style
E={"status":"EVIDENCE_FOUND","topic":"量子コンピュータ",
   "evidence_span":"量子コンピュータは量子力学の原理を計算に応用する。",
   "source":"https://example.org/source","verified":False,"train_ready":False,"promoted":False}
class PersonaPriorityTests(unittest.TestCase):
 def test_nagato(self):
  r=apply("今日は量子コンピュータの記事を読んだ",E)
  self.assertEqual(r["persona"],"nagato")
  self.assertIn("とある。",r["answer"])
 def test_neutral(self):
  r=apply("今日は量子コンピュータの記事を読んだ",E,persona="neutral")
  self.assertIn("記載されています。",r["answer"])
 def test_distinct_persona(self):
  a=apply("今日は量子コンピュータの記事を読んだ",E)
  b=apply("今日は量子コンピュータの記事を読んだ",E,persona="neutral")
  self.assertNotEqual(a["answer"],b["answer"])
 def test_same_evidence(self):
  for persona in ("nagato","neutral"):
   r=apply("今日は量子コンピュータの記事を読んだ",E,persona=persona)
   self.assertIn(E["evidence_span"],r["answer"])
   self.assertEqual(r["source"],E["source"])
 def test_explicit_topic(self):
  r=apply("今日は量子コンピュータの記事を読んだ",E,explicit=True)
  self.assertEqual(r["response_intent"],"TOPIC_LOOKUP")
 def test_no_promote(self):
  r=apply("記事",E)
  self.assertFalse(r["verified"]);self.assertFalse(r["train_ready"]);self.assertFalse(r["promoted"])
 def test_unavailable(self):
  x={"status":"EVIDENCE_UNAVAILABLE"}
  self.assertIs(apply("記事",x),x)
 def test_invalid_persona_fallback(self):
  self.assertEqual(style("invalid")["persona"],"neutral")
 def test_chat_integration(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(s);self.assertIn("cha_persona_wiki_repair(previous,result",s)
  self.assertIn("persona=cha_wiki_conversation.persona",s)
if __name__=="__main__":unittest.main()
