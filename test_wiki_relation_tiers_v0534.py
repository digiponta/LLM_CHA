import ast
import unittest
from pathlib import Path
from wiki_relation_tiers_v0534 import classify,assess_why
S="超伝導量子干渉計 (SQUID) とは、ジョセフソン接合を含む環状超伝導体に基く、極めて弱い磁場の検出に用いられる非常に感度の高い磁気センサの一種である。"
URL="https://ja.wikipedia.org/wiki/超伝導量子干渉計"
class RelationTiersTests(unittest.TestCase):
 def test_means(self):
  self.assertEqual([r["relation"] for r in classify(S,URL)],["MEANS","MEANS"])
 def test_means_objects(self):
  self.assertEqual([r["object"] for r in classify(S,URL)],["ジョセフソン接合","環状超伝導体"])
 def test_no_fabricated_enables(self):
  self.assertFalse(any(r["relation"]=="ENABLES" for r in classify(S,URL)))
 def test_no_fabricated_causes(self):
  self.assertFalse(any(r["relation"]=="CAUSES" for r in classify(S,URL)))
 def test_question_assessment(self):
  r=assess_why("なぜ高感度なの？",S,URL)
  self.assertEqual(r["status"],"MEANS_PARTIAL")
  self.assertEqual(r["means_count"],2)
  self.assertFalse(r["causal_answer_approved"])
 def test_explicit_enables(self):
  r=classify("量子干渉によって微弱な磁場の検出が可能になる",URL)
  self.assertEqual(r[0]["relation"],"ENABLES")
 def test_explicit_causes(self):
  r=classify("回路の故障が原因で測定誤差が生じる",URL)
  self.assertEqual(r[0]["relation"],"CAUSES")
 def test_explicit_not_automatic_answer(self):
  r=assess_why("なぜ高感度なの？","回路の故障が原因で測定誤差が生じる",URL)
  self.assertFalse(r["causal_answer_approved"])
 def test_provenance(self):
  self.assertTrue(all(r["source"]==URL and not r["verified"] for r in classify(S,URL)))
 def test_no_training(self):
  self.assertTrue(all(not r["train_ready"] and not r["promoted"] for r in classify(S,URL)))
 def test_unrelated(self):
  self.assertEqual(assess_why("何を検出する？",S,URL)["status"],"NOT_APPLICABLE")
 def test_no_relation(self):
  self.assertEqual(assess_why("なぜ高感度なの？","無関係の文章。",URL)["status"],"NO_RELATION_EVIDENCE")
 def test_chat_syntax(self):
  s=(Path(__file__).parent/"chat.py").read_text(encoding="utf-8")
  ast.parse(s)
  self.assertIn("wiki_relation_tiers=",s)
if __name__=="__main__":unittest.main()
